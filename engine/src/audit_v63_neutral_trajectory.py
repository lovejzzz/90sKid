#!/usr/bin/env python3
"""Audit V63's 2383 view-neutral coordinate without fitting a look."""

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
import v62_profile
import v63_profile
from audit_t003_colorchecker import BRADFORD, D50_XYZ, lab_to_xyz_d50, xyz_to_lab_d50


ENGINE = Path(__file__).resolve().parents[1]
V62_LATTICE = ENGINE / "cache/print_2383_monitor_output_lut_193_v62.npy"
V63_LATTICE = ENGINE / "cache/print_2383_monitor_output_lut_193_v63.npy"
T003_AUDIT = (
    ENGINE
    / "research_runs/2026-08-06_t003_colorchecker/frame160_audit/t003_dkc_pro_audit.json"
)
REC709_TO_XYZ_D65 = np.asarray(
    [
        [0.4123907993, 0.3575843394, 0.1804807884],
        [0.2126390059, 0.7151686788, 0.0721923154],
        [0.0193308187, 0.1191947798, 0.9505321522],
    ],
    dtype=np.float64,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def neutral_records() -> tuple[np.ndarray, np.ndarray]:
    stops = np.linspace(-12.0, 9.0, 337, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    scene = np.repeat(levels[:, None], 3, axis=1)
    film = e.vgamut_to_balanced_film_rgb(e.bt2020_to_panasonic_vgamut(scene))
    records = e.develop_5279_record_density(e.film_records_from_rgb(film))
    return stops, records


def neutral_metrics(profile, authority: str) -> dict[str, object]:
    profile.apply(e)
    e.PRINT_MONITOR_COLOUR_AUTHORITY = authority
    e.refresh_5279_spectral_observer_caches()
    stops, records = neutral_records()
    output = e.render_2383_monitor_projection_from_record_density(records)
    lab = e.linear_rec709_to_oklab(np.maximum(output, 0.0))
    chroma = np.linalg.norm(lab[..., 1:3], axis=-1)
    mask = (lab[..., 0] >= 0.01) & (lab[..., 0] <= 0.99)
    channel_spread = np.max(output, axis=-1) - np.min(output, axis=-1)
    return {
        "authority": authority,
        "policy": e.PRINT_2383_VIEW_NEUTRAL_POLICY,
        "usable_stop_range": [float(stops[mask][0]), float(stops[mask][-1])],
        "oklab_chroma_median": float(np.median(chroma[mask])),
        "oklab_chroma_p95": float(np.percentile(chroma[mask], 95)),
        "oklab_chroma_maximum": float(np.max(chroma[mask])),
        "linear_rgb_channel_spread_p95": float(
            np.percentile(channel_spread[mask], 95)
        ),
        "linear_rgb_channel_spread_maximum": float(np.max(channel_spread[mask])),
    }


def density_neutral_shaper_audit() -> dict[str, object]:
    v62_profile.apply(e)
    stops = np.linspace(-12.0, 9.0, 337, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    scene = np.repeat(levels[:, None], 3, axis=1)
    negative = e.negative_total_printer_density(scene)
    raw = e._raw_print_2383_density_from_negative(negative)
    shaped = e.print_2383_density_from_negative(negative)
    delta = shaped - raw
    return {
        "maximum_absolute_density_change_D_rgb": np.max(
            np.abs(delta), axis=0
        ).tolist(),
        "rms_density_change_D_rgb": np.sqrt(np.mean(delta * delta, axis=0)).tolist(),
        "classification": (
            "H-61-inspired continuous neutral-scale inference; not six measured "
            "off-LAD Status-A triplets"
        ),
    }


def lattice_archive_gate(samples: int = 128) -> dict[str, object]:
    old = np.load(V62_LATTICE, mmap_mode="r")
    v62_profile.apply(e)
    rng = np.random.default_rng(5279)
    index = rng.integers(0, old.shape[0], size=(samples, 3))
    axis = np.linspace(
        -0.16, e.NEGATIVE_5279_MAX_RECORD_DENSITY, old.shape[0], dtype=np.float32
    )
    total = np.stack(
        [axis[index[:, 0]], axis[index[:, 1]], axis[index[:, 2]]], axis=-1
    ) + e.SENSITO_DMIN_RGB
    direct = e.render_2383_monitor_projection_from_record_density(total)
    archived = np.asarray(old[index[:, 0], index[:, 1], index[:, 2]])
    absolute = np.abs(direct - archived)
    return {
        "sampled_native_nodes": samples,
        "exactly_equal": bool(np.array_equal(direct, archived)),
        "maximum_absolute_difference": float(np.max(absolute)),
        "mean_absolute_difference": float(np.mean(absolute)),
        "v62_lattice_sha256": sha256(V62_LATTICE),
        "v63_lattice_sha256": sha256(V63_LATTICE),
    }


def difference_metrics(a: np.ndarray, b: np.ndarray) -> dict[str, float]:
    absolute = np.abs(np.asarray(a, dtype=np.float32) - np.asarray(b, dtype=np.float32))
    delta = np.linalg.norm(
        e.linear_rec709_to_oklab(np.maximum(a, 0.0))
        - e.linear_rec709_to_oklab(np.maximum(b, 0.0)),
        axis=-1,
    )
    return {
        "linear_rgb_mae": float(np.mean(absolute)),
        "linear_rgb_p95_absolute": float(np.percentile(absolute, 95)),
        "linear_rgb_p99_absolute": float(np.percentile(absolute, 99)),
        "linear_rgb_maximum_absolute": float(np.max(absolute)),
        "oklab_delta_median": float(np.median(delta)),
        "oklab_delta_p95": float(np.percentile(delta, 95)),
        "oklab_delta_p99": float(np.percentile(delta, 99)),
        "changed_12bit_component_fraction": float(
            np.mean(
                np.rint(np.clip(a, 0.0, 1.0) * 4095.0)
                != np.rint(np.clip(b, 0.0, 1.0) * 4095.0)
            )
        ),
    }


def decode_reduced(source: Path, decoder: Path, frame: int, width: int, height: int) -> np.ndarray:
    payload = subprocess.check_output(
        [str(decoder), str(source), str(frame), "1"], stderr=subprocess.DEVNULL
    )
    expected = 5760 * 4320 * 3 * 4
    if len(payload) != expected:
        raise RuntimeError(f"decoder returned {len(payload)} bytes; expected {expected}")
    native = np.frombuffer(payload, dtype="<f4").reshape(4320, 5760, 3)
    reduced = cv2.resize(native, (width, height), interpolation=cv2.INTER_AREA)
    del native, payload
    gc.collect()
    return reduced.astype(np.float32)


def render_deterministic(profile, raw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    profile.apply(e)
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    records = e.develop_5279_record_density(e.film_records_from_rgb(film))
    projection = e.render_2383_monitor_projection_from_record_density(records)
    scan = e.render_cineon_scan_master_from_record_density(records)
    return projection, scan


def real_frame_audit(
    source: Path, decoder: Path, frame: int, width: int, height: int
) -> dict[str, object]:
    started = time.perf_counter()
    raw = decode_reduced(source, decoder, frame, width, height)
    v62_projection, v62_scan = render_deterministic(v62_profile, raw)
    v63_projection, v63_scan = render_deterministic(v63_profile, raw)
    return {
        "source": str(source),
        "frame": frame,
        "working_dimensions": [width, height],
        "seconds": time.perf_counter() - started,
        "projection_v62_vs_v63": difference_metrics(v62_projection, v63_projection),
        "scan_v62_vs_v63": difference_metrics(v62_scan, v63_scan),
    }


def output_chart_diagnostic(output: np.ndarray, reference_lab: np.ndarray) -> dict[str, object]:
    xyz = np.asarray(output, dtype=np.float64) @ REC709_TO_XYZ_D65.T
    neutral_xyz = xyz[1:4]
    source_white = np.mean(neutral_xyz / np.maximum(neutral_xyz[:, 1:2], 1e-12), axis=0)
    adaptation = (
        np.linalg.inv(BRADFORD)
        @ np.diag((BRADFORD @ D50_XYZ) / (BRADFORD @ source_white))
        @ BRADFORD
    )
    adapted = (adaptation @ xyz.T).T
    reference_xyz = np.asarray([lab_to_xyz_d50(value) for value in reference_lab])
    normalized = adapted * (
        reference_xyz[:, 1] / np.maximum(adapted[:, 1], 1e-12)
    )[:, None]
    measured_lab = np.asarray([xyz_to_lab_d50(value) for value in normalized])
    reference_hue = np.degrees(np.arctan2(reference_lab[:, 2], reference_lab[:, 1]))
    measured_hue = np.degrees(np.arctan2(measured_lab[:, 2], measured_lab[:, 1]))
    hue_error = (measured_hue - reference_hue + 180.0) % 360.0 - 180.0
    reference_chroma = np.linalg.norm(reference_lab[:, 1:3], axis=-1)
    measured_chroma = np.linalg.norm(measured_lab[:, 1:3], axis=-1)

    def group(indices: np.ndarray) -> dict[str, float]:
        return {
            "median_absolute_hue_error_degrees": float(
                np.median(np.abs(hue_error[indices]))
            ),
            "maximum_absolute_hue_error_degrees": float(
                np.max(np.abs(hue_error[indices]))
            ),
            "median_chroma_ratio": float(
                np.median(measured_chroma[indices] / reference_chroma[indices])
            ),
        }

    return {
        "synthetic_primaries_7_to_12": group(np.arange(6, 12)),
        "natural_colours_13_to_18": group(np.arange(12, 18)),
        "assumption": (
            "D50/Bradford diagnostic only; the outdoor scene SPD and the DGK "
            "manufacturer Lab illuminant/observer are not identified"
        ),
    }


def chart_authority_experiment() -> dict[str, object]:
    document = json.loads(T003_AUDIT.read_text(encoding="utf-8"))
    scene = np.asarray(
        [row["decoded_linear_bt2020_median"] for row in document["patches"]],
        dtype=np.float32,
    )
    reference = np.asarray(
        [row["manufacturer_CIELAB_as_published"] for row in document["patches"]],
        dtype=np.float64,
    )
    outputs = {}
    for name, authority in (
        ("scan_referenced", "scan_referenced_v31"),
        ("physical_spectral", "physical_spectral_v56"),
    ):
        v63_profile.apply(e)
        e.PRINT_MONITOR_COLOUR_AUTHORITY = authority
        e.refresh_5279_spectral_observer_caches()
        film = e.scene_to_5279_film_rgb(
            scene,
            exposure_stops=0.45,
            raw_colour="panasonic_official",
            include_optical_scatter=False,
            sensor_noise_treatment="photochemical",
        )
        records = e.develop_5279_record_density(e.film_records_from_rgb(film))
        output = e.render_2383_monitor_projection_from_record_density(records)
        outputs[name] = output_chart_diagnostic(output, reference)
    return {
        "source": str(T003_AUDIT),
        "observers": outputs,
        "decision_rule": (
            "Do not promote physical off-neutral colour unless it improves both "
            "synthetic and natural groups under a controlled, documented target."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"
        ),
    )
    parser.add_argument("--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode"))
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--skip-real-frame", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {
        "audit": "V63 actual 5279-to-2383 neutral trajectory coordinate audit",
        "archive_compatibility": lattice_archive_gate(),
        "density_neutral_shaper": density_neutral_shaper_audit(),
        "neutral_trajectory": {
            "v62_scan_referenced": neutral_metrics(
                v62_profile, "scan_referenced_v31"
            ),
            "v62_physical_spectral": neutral_metrics(
                v62_profile, "physical_spectral_v56"
            ),
            "v63_scan_referenced": neutral_metrics(
                v63_profile, "scan_referenced_v31"
            ),
            "v63_physical_spectral": neutral_metrics(
                v63_profile, "physical_spectral_v56"
            ),
        },
        "t003_chart_authority_experiment": chart_authority_experiment(),
        "decision": {
            "accepted": (
                "Replace only the obsolete equal-principal-density projected-gray "
                "coordinate with the complete neutral 5279-to-2383 trajectory."
            ),
            "frozen": (
                "Keep scan-referenced off-neutral colour; the physical spectral "
                "branch is not validated by the uncontrolled T003 chart."
            ),
            "still_unidentified": (
                "six off-LAD Status-A gray triplets, 5279-to-2383 separated-exposure "
                "interimage coefficients, and a measured theatre appearance target"
            ),
        },
    }
    if not args.skip_real_frame:
        report["real_frame"] = real_frame_audit(
            args.source, args.decoder, args.frame, args.width, args.height
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
