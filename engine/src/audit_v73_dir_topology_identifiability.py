#!/usr/bin/env python3
"""Audit the evidence boundary of the active 5279 DIR topology.

The public 5279 sheet does not disclose separation-wedge gammas or the
population-specific developer-inhibitor recipe.  This audit therefore does
not fit a replacement.  It expands the current prior into its complete
record/population transport tensor, measures its deterministic Jacobian and
performs a same-frame zero-DIR ablation so that its actual ownership is
visible.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import gc
import json
from pathlib import Path
import subprocess
import time

import cv2
import numpy as np

import emulsion_experiment as e
import v72_profile
from audit_v63_neutral_trajectory import difference_metrics
from audit_v71_record_coupling_ownership import (
    finite_difference_jacobian,
    summarize_jacobian,
)


RECORDS = ("red_cyan", "green_magenta", "blue_yellow")
POPULATIONS = ("fast", "medium", "slow")
DEFAULT_LOG_EXPOSURES = (-3.0, -2.5, -1.0, 0.0)
FILM_IMAGE_WIDTH_MM = 24.9
NATIVE_WIDTH_PX = 5760


@contextmanager
def interimage_strength(value: float):
    original = float(e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH)
    e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH = float(value)
    try:
        yield
    finally:
        e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH = original


def effective_transport_tensor() -> np.ndarray:
    """Return destination-record/source-record/destination-pop/source-pop."""
    tensor = np.zeros((3, 3, 3, 3), dtype=np.float64)
    for destination_record in range(3):
        for source_record in range(3):
            for destination_population in range(3):
                for source_population in range(3):
                    tensor[
                        destination_record,
                        source_record,
                        destination_population,
                        source_population,
                    ] = (
                        e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH
                        * e.DIR_INTERIMAGE_RECEIVER_CAUSER[
                            destination_record, source_record
                        ]
                        * e.DIR_POPULATION_TRANSPORT[
                            destination_population, source_population
                        ]
                        * e.DIR_POPULATION_RELEASE_GAIN[source_population]
                        * e.DIR_POPULATION_RECEIVER_GAIN[destination_population]
                    )
    return tensor


def normalized_shares(values: np.ndarray, axis: tuple[int, ...]) -> list[float]:
    sums = np.sum(values, axis=axis)
    return (sums / np.maximum(np.sum(sums), 1.0e-30)).tolist()


def topology_report() -> dict[str, object]:
    tensor = effective_transport_tensor()
    record_pair = np.sum(tensor, axis=(2, 3))
    adjacent_mask = np.zeros((3, 3), dtype=bool)
    remote_mask = np.zeros((3, 3), dtype=bool)
    for destination, source in ((0, 1), (1, 0), (1, 2), (2, 1)):
        adjacent_mask[destination, source] = True
    for destination, source in ((0, 2), (2, 0)):
        remote_mask[destination, source] = True
    adjacent_mean = float(np.mean(record_pair[adjacent_mask]))
    remote_mean = float(np.mean(record_pair[remote_mask]))

    pitch_um = FILM_IMAGE_WIDTH_MM * 1000.0 / NATIVE_WIDTH_PX
    sigma_um = e.DIR_POPULATION_LATERAL_SIGMA_PX_5760 * pitch_um
    return {
        "orientation": (
            "destination record, source record, destination population, "
            "source population"
        ),
        "record_order": list(RECORDS),
        "population_order": list(POPULATIONS),
        "nonzero_cross_record_population_edges": int(np.count_nonzero(tensor)),
        "possible_cross_record_population_edges": 6 * 3 * 3,
        "effective_transport_tensor": tensor.tolist(),
        "summed_record_pair_matrix_destination_by_source": record_pair.tolist(),
        "adjacent_record_pair_mean": adjacent_mean,
        "remote_red_blue_pair_mean": remote_mean,
        "adjacent_to_remote_ratio": adjacent_mean / max(remote_mean, 1.0e-30),
        "source_population_share": normalized_shares(tensor, (0, 1, 2)),
        "receiver_population_share": normalized_shares(tensor, (0, 1, 3)),
        "lateral_scale": {
            "assumed_film_image_width_mm": FILM_IMAGE_WIDTH_MM,
            "native_width_px": NATIVE_WIDTH_PX,
            "micrometres_per_pixel": pitch_um,
            "sigma_px_fast_medium_slow": (
                e.DIR_POPULATION_LATERAL_SIGMA_PX_5760.tolist()
            ),
            "sigma_micrometres_fast_medium_slow": sigma_um.tolist(),
            "fwhm_micrometres_fast_medium_slow": (2.35482 * sigma_um).tolist(),
        },
        "classification": (
            "Dense, restrained prior: every cross-record population pair is "
            "nonzero. Period Kodak patents support mobile, adjacent-layer and "
            "population-selective DIR chemistry, but do not identify this "
            "complete tensor as the 5279 recipe."
        ),
    }


def jacobian_report(log_exposures: tuple[float, ...], step: float) -> dict[str, object]:
    rows: dict[str, list[dict[str, object]]] = {}
    for condition, strength in (
        ("current_dir", float(e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH)),
        ("zero_interimage_dir", 0.0),
    ):
        values = []
        with interimage_strength(strength):
            for log_exposure in log_exposures:
                values.append(
                    {
                        "log_exposure": log_exposure,
                        "developed_status_m_record_density": summarize_jacobian(
                            finite_difference_jacobian(
                                log_exposure,
                                "developed_status_m_record_density",
                                step,
                            )
                        ),
                        "negative_printer_density": summarize_jacobian(
                            finite_difference_jacobian(
                                log_exposure,
                                "negative_printer_density",
                                step,
                            )
                        ),
                    }
                )
        rows[condition] = values

    maximum_neutral_gamma_delta = 0.0
    maximum_separation_ratio_delta = 0.0
    maximum_current_developed_off_diagonal = 0.0
    maximum_current_printer_off_diagonal = 0.0
    for current, zero in zip(
        rows["current_dir"], rows["zero_interimage_dir"], strict=True
    ):
        for stage in ("developed_status_m_record_density", "negative_printer_density"):
            current_stage = current[stage]
            zero_stage = zero[stage]
            maximum_neutral_gamma_delta = max(
                maximum_neutral_gamma_delta,
                float(
                    np.max(
                        np.abs(
                            np.asarray(current_stage["signed_neutral_gamma_row_sum"])
                            - np.asarray(zero_stage["signed_neutral_gamma_row_sum"])
                        )
                    )
                ),
            )
            maximum_separation_ratio_delta = max(
                maximum_separation_ratio_delta,
                float(
                    np.max(
                        np.abs(
                            np.asarray(current_stage["separation_to_neutral_gamma_ratio"])
                            - np.asarray(zero_stage["separation_to_neutral_gamma_ratio"])
                        )
                    )
                ),
            )
            if stage == "developed_status_m_record_density":
                maximum_current_developed_off_diagonal = max(
                    maximum_current_developed_off_diagonal,
                    float(current_stage["maximum_absolute_off_diagonal"]),
                )
            else:
                maximum_current_printer_off_diagonal = max(
                    maximum_current_printer_off_diagonal,
                    float(current_stage["maximum_absolute_off_diagonal"]),
                )
    return {
        "central_difference_step_loge": step,
        "log_exposures": list(log_exposures),
        "conditions": rows,
        "summary": {
            "maximum_neutral_gamma_delta_current_vs_zero": (
                maximum_neutral_gamma_delta
            ),
            "maximum_separation_to_neutral_gamma_ratio_delta": (
                maximum_separation_ratio_delta
            ),
            "maximum_current_developed_status_m_absolute_off_diagonal": (
                maximum_current_developed_off_diagonal
            ),
            "maximum_current_printer_density_absolute_off_diagonal": (
                maximum_current_printer_off_diagonal
            ),
        },
        "measurement_warning": (
            "These are internal finite-difference derivatives of the engine's "
            "record coordinate. They expose model ownership; they are not a "
            "substitute for Kodak 5279 separation-exposure and white-light "
            "wedge gammas measured under one process."
        ),
    }


def decode_reduced(
    source: Path, decoder: Path, frame: int, width: int, height: int
) -> np.ndarray:
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


def render_condition(raw: np.ndarray, strength: float) -> tuple[np.ndarray, np.ndarray]:
    v72_profile.apply(e)
    with interimage_strength(strength):
        film = e.scene_to_5279_film_rgb(
            raw,
            exposure_stops=0.45,
            raw_colour="panasonic_official",
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.develop_5279_record_density(e.film_records_from_rgb(film))
        return (
            e.render_2383_monitor_projection_from_record_density(records),
            e.render_cineon_scan_master_from_record_density(records),
        )


def real_frame_report(
    source: Path, decoder: Path, frame: int, width: int, height: int
) -> dict[str, object]:
    started = time.perf_counter()
    raw = decode_reduced(source, decoder, frame, width, height)
    current_strength = float(e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH)
    current_projection, current_scan = render_condition(raw, current_strength)
    zero_projection, zero_scan = render_condition(raw, 0.0)
    return {
        "source": str(source),
        "frame": frame,
        "working_dimensions": [width, height],
        "deterministic_no_grain": True,
        "seconds": time.perf_counter() - started,
        "current_vs_zero_dir": {
            "projection": difference_metrics(current_projection, zero_projection),
            "managed_scan": difference_metrics(current_scan, zero_scan),
        },
    }


def measure(
    *,
    log_exposures: tuple[float, ...],
    step: float,
    source: Path | None,
    decoder: Path,
    frame: int,
    width: int,
    height: int,
) -> dict[str, object]:
    v72_profile.apply(e)
    report: dict[str, object] = {
        "audit": "V73 5279 DIR topology identifiability",
        "profile": v72_profile.PROFILE["name"],
        "image_change": "none",
        "topology": topology_report(),
        "deterministic_jacobian": jacobian_report(log_exposures, step),
        "evidence_boundary": {
            "stock_specific_public": (
                "5279 neutral characteristic curves, processed-stock MTF, "
                "spectral sensitivity, net dye density and per-record 48 um RMS"
            ),
            "period_architecture_witness": (
                "two/three speed populations, fastest farthest from support, "
                "mobile DIR interaction with adjacent units, asymmetric and "
                "population-selective coupler placement"
            ),
            "not_publicly_identified_for_5279": (
                "separation-wedge gamma ratios, exact DIR source/receiver "
                "populations, inhibitor diffusion/scavenging distances and "
                "frequency-resolved effect on record covariance"
            ),
        },
        "decision": (
            "Retain the current restrained DIR mechanism in V72 because it owns "
            "a distinct, period-supported chemical observable, but classify its "
            "dense population tensor as an unmeasured prior. Do not promote a "
            "zero-DIR or patent-shaped replacement without stock-specific "
            "separation/white-light wedges or controlled 5279 scans."
        ),
    }
    if source is not None:
        report["real_frame_ablation"] = real_frame_report(
            source, decoder, frame, width, height
        )
    return report


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
    parser.add_argument(
        "--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode")
    )
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--skip-real-frame", action="store_true")
    parser.add_argument("--step", type=float, default=1.0e-3)
    parser.add_argument(
        "--log-exposures",
        nargs="+",
        type=float,
        default=list(DEFAULT_LOG_EXPOSURES),
    )
    args = parser.parse_args()
    result = measure(
        log_exposures=tuple(args.log_exposures),
        step=args.step,
        source=None if args.skip_real_frame else args.source,
        decoder=args.decoder,
        frame=args.frame,
        width=args.width,
        height=args.height,
    )
    payload = json.dumps(result, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
