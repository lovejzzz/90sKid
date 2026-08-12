#!/usr/bin/env python3
"""Audit 2383 interimage stage ownership after V61's Status-M correction.

This script does not fit a look.  It compares the archived cross-vendor
surrogate with the minimum-assumption identity endpoint, reports local
Jacobians at every physical stage, and measures the resulting difference on a
real GH7 frame.  It also checks whether V61's direct observer agrees with the
V60 lattice that the production graph still used for its pointwise grain
delta.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import time

import cv2
import numpy as np

import emulsion_experiment as e
import v60_profile
import v61_profile
import v62_profile


ARCHIVE_MATRIX = np.asarray(
    [
        [1.4105, -0.9566, 0.9152],
        [0.4127, 0.6943, -0.2324],
        [-0.5640, 0.6093, 0.8425],
    ],
    dtype=np.float32,
)
IDENTITY_MATRIX = np.eye(3, dtype=np.float32)
VENDOR_ANALYZER = (
    Path(__file__).resolve().parents[1]
    / "research_runs/2026-08-03_vendor_2383_targets/analyze_vendor_luts.py"
)
VENDOR_METRICS = VENDOR_ANALYZER.with_name("metrics.json")
V60_LATTICE = (
    Path(__file__).resolve().parents[1]
    / "cache/print_2383_monitor_output_lut_193_v60.npy"
)
V62_LATTICE = (
    Path(__file__).resolve().parents[1]
    / "cache/print_2383_monitor_output_lut_193_v62.npy"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_normalized(matrix: np.ndarray) -> np.ndarray:
    diagonal = np.diag(matrix)
    divisor = np.where(np.abs(diagonal) > 1e-12, diagonal, 1.0)
    return matrix / divisor[:, None]


def finite_jacobian(function, point: np.ndarray, step: float = 1e-3) -> np.ndarray:
    point = np.asarray(point, dtype=np.float32)
    columns = []
    for channel in range(3):
        offset = np.zeros(3, dtype=np.float32)
        offset[channel] = step
        columns.append(
            (
                np.asarray(function(point + offset), dtype=np.float64)
                - np.asarray(function(point - offset), dtype=np.float64)
            )
            / (2.0 * step)
        )
    return np.column_stack(columns)


def neutral_total_density(stop: float) -> np.ndarray:
    scene = np.full((1, 1, 3), 0.18 * (2.0**stop), dtype=np.float32)
    film = e.vgamut_to_balanced_film_rgb(e.bt2020_to_panasonic_vgamut(scene))
    return e.develop_5279_record_density(e.film_records_from_rgb(film))[0, 0]


def print_log_exposure(negative_printer_density: np.ndarray) -> np.ndarray:
    neutral_negative = e.negative_total_printer_density(
        np.asarray([0.18, 0.18, 0.18], dtype=np.float32)
    )
    lad = e._active_2383_lad_principal_density_rgb()
    aim = np.asarray(
        [e._inverse_2383_density(channel, float(lad[channel])) for channel in range(3)],
        dtype=np.float32,
    )
    captured = neutral_negative + aim - negative_printer_density
    return (
        aim
        + np.einsum(
            "...c,dc->...d",
            captured - aim,
            e.PRINT_2383_INTERIMAGE_MATRIX,
        )
    ).astype(np.float32)


def stages(total_density: np.ndarray) -> dict[str, np.ndarray]:
    negative = e.negative_total_printer_density_from_record_density(total_density)
    raw_print = e._raw_print_2383_density_from_negative(negative)
    shaped_print = e.print_2383_density_from_negative(negative)
    physical = e._render_2383_projection_uncalibrated_from_print_density(
        shaped_print[None, None]
    )[0, 0]
    monitor = e.render_2383_monitor_projection_from_record_density(
        total_density[None, None]
    )[0, 0]
    return {
        "negative_printer_density": negative,
        "print_log_exposure": print_log_exposure(negative),
        "raw_print_principal_density": raw_print,
        "neutral_shaped_print_principal_density": shaped_print,
        "physical_projection_linear_rgb": physical,
        "monitor_projection_linear_rgb": monitor,
    }


def local_stage_audit(matrix: np.ndarray) -> dict[str, object]:
    e.PRINT_2383_INTERIMAGE_MATRIX = np.asarray(matrix, dtype=np.float32).copy()
    e.refresh_5279_spectral_observer_caches()
    rows: dict[str, object] = {}
    for stop in (-4.0, -2.0, 0.0, 2.0, 4.0):
        point = neutral_total_density(stop)
        values = stages(point)
        stage_rows = {}
        for name, value in values.items():
            jacobian = finite_jacobian(lambda sample: stages(sample)[name], point)
            stage_rows[name] = {
                "value": np.asarray(value, dtype=np.float64).tolist(),
                "jacobian": jacobian.tolist(),
                "row_normalized_jacobian": row_normalized(jacobian).tolist(),
                "maximum_absolute_row_normalized_off_diagonal": float(
                    np.max(np.abs(row_normalized(jacobian) - np.eye(3)))
                ),
            }
        rows[f"{stop:+.0f}"] = {
            "neutral_scene_stop_from_18_percent": stop,
            "total_status_m_density_rgb": point.tolist(),
            "stages": stage_rows,
        }
    return rows


def decode_reduced_frame(
    source: Path, decoder: Path, frame: int, width: int, height: int
) -> np.ndarray:
    result = subprocess.run(
        [str(decoder), str(source), str(frame), "1"],
        check=True,
        capture_output=True,
    )
    expected = 5760 * 4320 * 3 * 4
    if len(result.stdout) != expected:
        raise RuntimeError(
            f"decoder returned {len(result.stdout)} bytes; expected {expected}"
        )
    native = np.frombuffer(result.stdout, dtype="<f4").reshape(4320, 5760, 3)
    reduced = cv2.resize(
        native, (width, height), interpolation=cv2.INTER_AREA
    ).astype(np.float32)
    del native, result
    gc.collect()
    return reduced


def difference_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    absolute = np.abs(np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32))
    lab_a = e.linear_rec709_to_oklab(np.maximum(a, 0.0))
    lab_b = e.linear_rec709_to_oklab(np.maximum(b, 0.0))
    delta_e = np.linalg.norm(lab_a - lab_b, axis=-1)
    quantized_a = np.rint(np.clip(a, 0.0, 1.0) * 4095.0)
    quantized_b = np.rint(np.clip(b, 0.0, 1.0) * 4095.0)
    return {
        "linear_rgb_mae": float(np.mean(absolute)),
        "linear_rgb_p95_absolute": float(np.percentile(absolute, 95)),
        "linear_rgb_p99_absolute": float(np.percentile(absolute, 99)),
        "linear_rgb_maximum_absolute": float(np.max(absolute)),
        "oklab_delta_median": float(np.percentile(delta_e, 50)),
        "oklab_delta_p95": float(np.percentile(delta_e, 95)),
        "oklab_delta_p99": float(np.percentile(delta_e, 99)),
        "changed_12bit_component_fraction": float(np.mean(quantized_a != quantized_b)),
    }


def density_difference_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    absolute = np.abs(
        np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32)
    )
    return {
        "density_mae": float(np.mean(absolute)),
        "density_p95_absolute": float(np.percentile(absolute, 95)),
        "density_p99_absolute": float(np.percentile(absolute, 99)),
        "density_maximum_absolute": float(np.max(absolute)),
        "component_fraction_changed_over_1e_5D": float(
            np.mean(absolute > 1e-5)
        ),
    }


def sample_difference_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    absolute = np.abs(
        np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32)
    )
    return {
        "sample_mae": float(np.mean(absolute)),
        "sample_p95_absolute": float(np.percentile(absolute, 95)),
        "sample_p99_absolute": float(np.percentile(absolute, 99)),
        "sample_maximum_absolute": float(np.max(absolute)),
    }


def real_frame_audit(
    source: Path, decoder: Path, frame: int, width: int, height: int
) -> dict[str, object]:
    started = time.perf_counter()
    raw = decode_reduced_frame(source, decoder, frame, width, height)
    decoded_at = time.perf_counter()
    v61_profile.apply(e)
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    total_density = e.develop_5279_record_density(e.film_records_from_rgb(film))
    del raw, film
    gc.collect()
    formed_at = time.perf_counter()

    outputs: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    stage_seconds: dict[str, float] = {}
    for name, matrix in (("identity", IDENTITY_MATRIX), ("archive", ARCHIVE_MATRIX)):
        branch_started = time.perf_counter()
        e.PRINT_2383_INTERIMAGE_MATRIX = matrix.copy()
        e.refresh_5279_spectral_observer_caches()
        negative = e.negative_total_printer_density_from_record_density(total_density)
        print_density = e.print_2383_density_from_negative(negative)
        physical = e._render_2383_projection_uncalibrated_from_print_density(
            print_density
        )
        monitor = e.render_2383_monitor_projection_from_record_density(total_density)
        outputs[name] = (print_density, physical, monitor)
        stage_seconds[name] = time.perf_counter() - branch_started

    v60_lattice = np.load(V60_LATTICE, allow_pickle=False)
    v60_fast = e.sample_record_density_delta_lut(total_density, v60_lattice)
    archive_direct = outputs["archive"][2]
    identity_direct = outputs["identity"][2]

    # Establish the lattice's own interpolation floor separately from the V61
    # model mismatch.
    yy, xx = np.indices(total_density.shape[:2], dtype=np.float32)
    microscopic_delta = 0.002 * np.stack(
        [
            np.sin(xx * 0.137 + yy * 0.071),
            np.sin(xx * 0.091 - yy * 0.113 + 1.0),
            np.sin(xx * 0.053 + yy * 0.149 + 2.0),
        ],
        axis=-1,
    )
    perturbed_density = total_density + microscopic_delta.astype(np.float32)

    v60_profile.apply(e)
    v60_direct = e.render_2383_monitor_projection_from_record_density(total_density)
    v60_direct_perturbed = e.render_2383_monitor_projection_from_record_density(
        perturbed_density
    )
    v60_fast_perturbed = e.sample_record_density_delta_lut(
        perturbed_density, v60_lattice
    )

    v62_profile.apply(e)
    v62_lattice = np.load(V62_LATTICE, allow_pickle=False)
    v62_fast = e.sample_record_density_delta_lut(total_density, v62_lattice)
    v62_direct_perturbed = e.render_2383_monitor_projection_from_record_density(
        perturbed_density
    )
    v62_fast_perturbed = e.sample_record_density_delta_lut(
        perturbed_density, v62_lattice
    )

    result = {
        "source": str(source),
        "frame": frame,
        "working_dimensions": [width, height],
        "total_status_m_density_mean_rgb": np.mean(total_density, axis=(0, 1)).tolist(),
        "timing_seconds": {
            "decode_and_reduce": decoded_at - started,
            "deterministic_negative_formation": formed_at - decoded_at,
            "identity_observer": stage_seconds["identity"],
            "archive_observer": stage_seconds["archive"],
            "total": time.perf_counter() - started,
        },
        "identity_vs_archive": {
            "print_principal_density": density_difference_metrics(
                outputs["identity"][0], outputs["archive"][0]
            ),
            "physical_projection": difference_metrics(
                outputs["identity"][1], outputs["archive"][1]
            ),
            "monitor_projection": difference_metrics(
                identity_direct, archive_direct
            ),
        },
        "production_lattice_consistency": {
            "v60_direct_vs_v60_lattice_interpolation_floor": difference_metrics(
                v60_direct, v60_fast
            ),
            "v60_microscopic_density_delta_direct_vs_lattice_delta": (
                sample_difference_metrics(
                    v60_direct_perturbed - v60_direct,
                    v60_fast_perturbed - v60_fast,
                )
            ),
            "v61_archive_direct_vs_loaded_v60_lattice": difference_metrics(
                archive_direct, v60_fast
            ),
            "v61_identity_direct_vs_loaded_v60_lattice": difference_metrics(
                identity_direct, v60_fast
            ),
            "v62_direct_vs_v62_lattice": difference_metrics(
                identity_direct, v62_fast
            ),
            "v62_microscopic_density_delta_direct_vs_lattice_delta": (
                sample_difference_metrics(
                    v62_direct_perturbed - identity_direct,
                    v62_fast_perturbed - v62_fast,
                )
            ),
            "interpretation": (
                "V61's mean projection uses V61's direct model, while the "
                "archive-pointwise projection grain delta still samples this "
                "V60 lattice. V62 binds its profile-identical lattice so one "
                "observer owns both mean and microscopic density changes."
            ),
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "/Users/tianxing/Movies/test-proresRawlog/"
            "NJARAW_S001_S001_T020.MOV"
        ),
    )
    parser.add_argument(
        "--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode")
    )
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--skip-real-frame", action="store_true")
    args = parser.parse_args()

    v61_profile.apply(e)
    vendor_document = json.loads(VENDOR_METRICS.read_text(encoding="utf-8"))
    report: dict[str, object] = {
        "audit": "V62 2383 interimage stage-ownership audit",
        "question": (
            "Does the archived cross-vendor preview surrogate remain a valid "
            "positive-film interimage model after V61 corrected the negative "
            "Status-M/analytical coordinate?"
        ),
        "matrix_geometry": {
            "archive": ARCHIVE_MATRIX.tolist(),
            "identity": IDENTITY_MATRIX.tolist(),
            "archive_row_sums": np.sum(ARCHIVE_MATRIX, axis=1).tolist(),
            "archive_column_sums": np.sum(ARCHIVE_MATRIX, axis=0).tolist(),
            "archive_condition_number": float(np.linalg.cond(ARCHIVE_MATRIX)),
        },
        "fit_provenance": {
            "vendor_analyzer_sha256": sha256(VENDOR_ANALYZER),
            "vendor_metrics_sha256": sha256(VENDOR_METRICS),
            "source_hashes": vendor_document["sources"],
            "classification": (
                "Mixed finished-look transforms: Resolve Cineon-to-Rec.709, "
                "Adobe 5218-plus-2383, FilmVision looks without a documented "
                "input contract, and an AP0-to-AP0 ACES LMT. They are useful "
                "display brackets, not same-process 5279-to-2383 chemical "
                "measurements."
            ),
        },
        "primary_evidence_boundary": {
            "US20020118211A1": (
                "A chemical print-film interimage matrix must be identified "
                "from separated colour exposures, converted from Status-A to "
                "analytical density. Identity is the no-measurement/no-effect "
                "endpoint, not proof that real 2383 has no interimage effect."
            ),
            "US8654192B2": (
                "The LAD-anchored log-exposure placement is valid, but fitting "
                "requires DPX-to-theatre-Lab pairs from the same film workflow "
                "distributed through the input space, including saturated hues."
            ),
            "Ishii_2003": (
                "EK5279-to-EK2383 was measured with 401 patches and required a "
                "stock-specific 3x13 density polynomial; the paper does not "
                "publish the EK5279 coefficients."
            ),
        },
        "stage_local_jacobians": {
            "identity": local_stage_audit(IDENTITY_MATRIX),
            "archive": local_stage_audit(ARCHIVE_MATRIX),
        },
    }
    if not args.skip_real_frame:
        report["real_frame"] = real_frame_audit(
            args.source, args.decoder, args.frame, args.width, args.height
        )
    report["decision"] = {
        "archive_matrix": "withdraw from the evidence-corrected physical stage",
        "v62_physical_interimage_policy": (
            "identity minimum-assumption endpoint, explicitly unmeasured"
        ),
        "display_policy": (
            "do not move the old matrix into display; the current scan-referenced "
            "monitor boundary already owns its declared display colour"
        ),
        "required_pipeline_fix": (
            "build and bind a V62 193-cube observer lattice from the same V62 "
            "profile used for mean print formation"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
