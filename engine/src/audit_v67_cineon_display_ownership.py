#!/usr/bin/env python3
"""Audit ownership of the post-Cineon display and Blu-ray finish layers."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import time

import cv2
import numpy as np

import emulsion_experiment as e
import v66_profile
from audit_v66_scanner_printing_density import (
    code_metrics,
    decode_reduced,
    difference_metrics,
    luma_metrics,
)


def scanner_density_for_neutral(level: float) -> np.ndarray:
    rgb = np.full(3, level, dtype=np.float32)
    records = e.film_records_from_rgb(rgb)
    total = e.develop_5279_record_density(records)
    return e.scanner_density_from_total_record_density(total)


def display_map(
    scanner_density: np.ndarray,
    *,
    high_scene_level: float = 10.0,
    peak: float = 0.90,
    toe_width_density: float = 0.008,
) -> np.ndarray:
    """Parameterize the current display mapping without changing its math."""
    mid_density = 0.700
    # Use the engine-owned anchors for the current endpoint so this audit must
    # close bit-for-bit before any parameter is ablated. Recompute only an
    # intentionally changed high anchor.
    mid_scanner = e.NEUTRAL_MID_SCANNER_DENSITY
    high_scanner = (
        e.NEUTRAL_HIGH_SCANNER_DENSITY
        if high_scene_level == 10.0
        else scanner_density_for_neutral(high_scene_level)
    )
    gain = mid_density / np.maximum(mid_scanner, 1e-6)
    matched = np.asarray(scanner_density, dtype=np.float32) * gain
    code = np.clip(np.rint(95.0 + matched / 0.002), 0.0, 1023.0)
    decoded = (code - 95.0) * 0.002
    if toe_width_density > 0.0:
        decoded = 0.5 * (
            decoded + np.sqrt(decoded * decoded + toe_width_density**2)
        )
        high_density = high_scanner * gain
        high_density = 0.5 * (
            high_density
            + np.sqrt(high_density * high_density + toe_width_density**2)
        )
        mid_toe = 0.5 * (
            mid_density
            + math.sqrt(mid_density**2 + toe_width_density**2)
        )
    else:
        decoded = np.maximum(decoded, 0.0)
        high_density = np.maximum(high_scanner * gain, 1e-6)
        mid_toe = mid_density
    unit_density = decoded / np.maximum(high_density, 1e-6)
    mid_unit = mid_toe / np.maximum(high_density, 1e-6)
    peak_rgb = np.full(3, peak, dtype=np.float32)
    power = np.log(0.18 / peak_rgb) / np.log(np.maximum(mid_unit, 1e-5))
    mapped = peak_rgb * np.power(np.clip(unit_density, 0.0, 1.25), power)
    return e.compress_unit_gamut(mapped).astype(np.float32)


def neutral_scale() -> dict[str, list[float]]:
    stops = np.arange(-6.0, 7.0, 1.0, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    total = e.develop_5279_record_density(
        e.film_records_from_rgb(np.repeat(levels[:, None], 3, axis=1))
    )
    scanner = e.scanner_density_from_total_record_density(total)
    open_scan = e.render_cineon_scan_master_from_scanner_density(scanner)
    finished = e.finish_cineon_scan_for_bluray(open_scan)
    luma_open = np.einsum("...c,c->...", open_scan, [0.2126, 0.7152, 0.0722])
    luma_finish = np.einsum("...c,c->...", finished, [0.2126, 0.7152, 0.0722])
    return {
        "stops_from_18_percent": stops.astype(float).tolist(),
        "scene_linear": levels.astype(float).tolist(),
        "open_display_linear_luma": luma_open.astype(float).tolist(),
        "bluray_finish_linear_luma": luma_finish.astype(float).tolist(),
    }


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
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("engine/research_runs/v67_cineon_display_stills"),
    )
    args = parser.parse_args()

    started = time.perf_counter()
    v66_profile.apply(e)
    raw = decode_reduced(
        args.source, args.decoder, args.frame, args.width, args.height
    )
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    total = e.develop_5279_record_density(e.film_records_from_rgb(film))
    scanner = e.apply_spirit_2k_scan_aperture_to_density(
        e.scanner_density_from_total_record_density(total)
    )
    gain = 0.700 / np.maximum(e.NEUTRAL_MID_SCANNER_DENSITY, 1e-6)
    continuous_code = 95.0 + scanner * gain / 0.002

    current_open = e.render_cineon_scan_master_from_scanner_density(scanner)
    current_finish = e.finish_cineon_scan_for_bluray(current_open)
    parameterized_current = display_map(scanner)
    models = {
        "current_bluray_finish": current_finish,
        "current_open_display_map": current_open,
        "parameterized_current_display_map": parameterized_current,
        "current_map_without_subreference_soft_toe": display_map(
            scanner, toe_width_density=0.0
        ),
        "display_peak_1p00": display_map(scanner, peak=1.0),
        "high_anchor_scene_1p0": display_map(scanner, high_scene_level=1.0),
        "high_anchor_scene_4p0": display_map(scanner, high_scene_level=4.0),
    }

    args.image_dir.mkdir(parents=True, exist_ok=True)
    for name, image in models.items():
        signal = e.srgb_encode(np.clip(image, 0.0, 1.0))
        payload = np.rint(signal[..., ::-1] * 65535.0).astype(np.uint16)
        if not cv2.imwrite(str(args.image_dir / f"{name}.png"), payload):
            raise RuntimeError(f"failed to write {name} diagnostic")

    result = {
        "audit": "V67 Cineon display-layer ownership audit",
        "status": "research_only_no_image_profile",
        "source": str(args.source),
        "frame": args.frame,
        "working_dimensions": [args.width, args.height],
        "seconds": time.perf_counter() - started,
        "cineon_code_before_10bit_clamp": code_metrics(continuous_code),
        "parameterized_current_map_exactly_closes": bool(
            np.array_equal(parameterized_current, current_open)
        ),
        "neutral_scale": neutral_scale(),
        "models_vs_current_bluray_finish": {
            name: difference_metrics(image, current_finish)
            for name, image in models.items()
        },
        "model_luma": {
            name: luma_metrics(image) for name, image in models.items()
        },
        "ownership": {
            "standardized_or_calibration_aim": [
                "10-bit code range",
                "0.002 printing density per code value",
                "reference black aim code 95",
                "neutral LAD/mid aim code 445 (0.700 D above code 95)",
            ],
            "active_model_not_measured_device_fact": [
                "5279-to-2383 printing-density spectral integration",
                "Spirit 2048-line aperture prior",
                "neutral high reference generated from scene-linear 10.0",
            ],
            "viewing_or_finishing_choice": [
                "0.008 D sub-reference soft toe",
                "display peak placement 0.90",
                "power curve derived from the scene-10 high anchor",
                "lower-scale gamma 1.20",
                "finish fade between display luma 0.12 and 0.30",
            ],
        },
        "conclusion": (
            "Cineon defines density data, not a unique Rec.709 image. The "
            "current open display map and Blu-ray finish are explicit viewing "
            "policies; neither may be attributed to 5279 without a measured "
            "film-print emulation or a named graded-master reference."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
