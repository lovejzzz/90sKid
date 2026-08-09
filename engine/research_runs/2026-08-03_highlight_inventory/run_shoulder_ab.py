"""Controlled extreme-frame A/B for V21's unmeasured logE > 0 shoulder.

The candidate is a diagnostic lower bound, not a proposed 5279 curve: it holds
each record at its published logE=0 density for all higher exposures.  Thus the
A/B bounds how much the V21 +0.5/+1.0 extension can affect this source.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT = ROOT / "experiments" / "emulsion_reconstruction"
sys.path.insert(0, str(EXPERIMENT / "src"))
import emulsion_experiment as emulsion


INPUT = Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV")
DECODER = Path("/tmp/prores_raw_float_decode")
OUTPUT = Path(__file__).resolve().parent
FRAME_INDEX = 97
SOURCE_WIDTH = 5760
SOURCE_HEIGHT = 4320
TEST_WIDTH = 1440
TEST_HEIGHT = 1080
EXPOSURE_STOPS = 0.45

BASELINE_CURVES = emulsion.SENSITO_DENSITY_RGB.copy()
CANDIDATE_CURVES = BASELINE_CURVES.copy()
CANDIDATE_CURVES[:, 10:] = CANDIDATE_CURVES[:, 9:10]


def decode_frame() -> np.ndarray:
    expected = SOURCE_WIDTH * SOURCE_HEIGHT * 3 * 4
    result = subprocess.run(
        [str(DECODER), str(INPUT), str(FRAME_INDEX), "1"],
        check=True,
        stdout=subprocess.PIPE,
    )
    if len(result.stdout) != expected:
        raise RuntimeError(f"decoder returned {len(result.stdout)} bytes, expected {expected}")
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(
        SOURCE_HEIGHT, SOURCE_WIDTH, 3
    )
    return cv2.resize(raw, (TEST_WIDTH, TEST_HEIGHT), interpolation=cv2.INTER_AREA)


def reset_curve_dependent_state(curves: np.ndarray) -> None:
    emulsion.SENSITO_DENSITY_RGB = curves.copy()
    emulsion.SENSITO_DMIN_RGB = emulsion.SENSITO_DENSITY_RGB[:, 0]
    emulsion.NEGATIVE_5279_BASE_DENSITY_RGB = emulsion.SENSITO_DMIN_RGB.copy()
    emulsion.NEUTRAL_MID_SCANNER_DENSITY = (
        emulsion.scanner_density_from_total_record_density(
            emulsion.record_densities(
                emulsion.film_records_from_rgb(
                    np.array([0.18, 0.18, 0.18], dtype=np.float32)
                )
            )
        )
    )
    emulsion.NEUTRAL_HIGH_SCANNER_DENSITY = (
        emulsion.scanner_density_from_total_record_density(
            emulsion.record_densities(
                emulsion.film_records_from_rgb(
                    np.array([10.0, 10.0, 10.0], dtype=np.float32)
                )
            )
        )
    )
    emulsion._PRINT_2383_NEUTRAL_SHAPERS = None
    emulsion._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    emulsion._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    emulsion._PRINT_2383_MONITOR_DELTA_LUT = None


def render(raw: np.ndarray, curves: np.ndarray, look: str) -> np.ndarray:
    reset_curve_dependent_state(curves)
    return emulsion.reconstruct_through_emulsion(
        raw,
        FRAME_INDEX,
        grain_scale=1.0,
        oversample=1,
        exposure_stops=EXPOSURE_STOPS,
        look=look,
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )


def exposure_metrics(raw: np.ndarray) -> dict[str, object]:
    film_rgb = emulsion.scene_to_5279_film_rgb(
        raw,
        exposure_stops=EXPOSURE_STOPS,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    loge = np.log10(np.maximum(emulsion.film_records_from_rgb(film_rgb), 1e-8)) - 1.0
    return {
        "loge_max_rgb": np.max(loge, axis=(0, 1)).astype(float).tolist(),
        "loge_gt_0_percent_rgb": (
            100.0 * np.mean(loge > 0.0, axis=(0, 1))
        ).astype(float).tolist(),
        "loge_gt_0p5_percent_rgb": (
            100.0 * np.mean(loge > 0.5, axis=(0, 1))
        ).astype(float).tolist(),
    }


def to_srgb_u8(bt709: np.ndarray) -> np.ndarray:
    srgb = emulsion.srgb_encode(emulsion.bt709_decode(bt709))
    return np.rint(np.clip(srgb, 0.0, 1.0) * 255.0).astype(np.uint8)


def save_rgb(path: Path, image: np.ndarray) -> None:
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def compare(name: str, baseline: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    baseline_linear = emulsion.bt709_decode(baseline)
    candidate_linear = emulsion.bt709_decode(candidate)
    delta = candidate_linear - baseline_linear
    baseline_luma = np.einsum("...c,c->...", baseline_linear, [0.2126, 0.7152, 0.0722])
    candidate_luma = np.einsum("...c,c->...", candidate_linear, [0.2126, 0.7152, 0.0722])
    lab_a = emulsion.linear_rec709_to_oklab(np.clip(baseline_linear, 0.0, None))
    lab_b = emulsion.linear_rec709_to_oklab(np.clip(candidate_linear, 0.0, None))
    delta_e = np.linalg.norm(lab_b - lab_a, axis=-1)
    mse = float(np.mean(np.square(delta)))
    baseline_u8 = to_srgb_u8(baseline)
    candidate_u8 = to_srgb_u8(candidate)
    save_rgb(OUTPUT / f"baseline_{name}.png", baseline_u8)
    save_rgb(OUTPUT / f"candidate_{name}.png", candidate_u8)
    save_rgb(OUTPUT / f"ab_{name}.png", np.concatenate([baseline_u8, candidate_u8], axis=1))
    amplified = np.clip(0.5 + 24.0 * delta, 0.0, 1.0)
    save_rgb(
        OUTPUT / f"difference_x24_{name}.png",
        np.rint(amplified * 255).astype(np.uint8),
    )
    return {
        "linear_rgb_mae": float(np.mean(np.abs(delta))),
        "linear_rgb_max_abs": float(np.max(np.abs(delta))),
        "psnr_db": float("inf") if mse == 0.0 else float(-10.0 * np.log10(mse)),
        "oklab_delta_e_median": float(np.median(delta_e)),
        "oklab_delta_e_p95": float(np.percentile(delta_e, 95)),
        "oklab_delta_e_p99": float(np.percentile(delta_e, 99)),
        "luma_delta_median": float(np.median(candidate_luma - baseline_luma)),
        "luma_delta_p95_abs": float(
            np.percentile(np.abs(candidate_luma - baseline_luma), 95)
        ),
        "baseline_luma_p99": float(np.percentile(baseline_luma, 99)),
        "candidate_luma_p99": float(np.percentile(candidate_luma, 99)),
        "baseline_luma_max": float(np.max(baseline_luma)),
        "candidate_luma_max": float(np.max(candidate_luma)),
        "eight_bit_pixels_changed_percent": float(
            100.0 * np.mean(np.any(baseline_u8 != candidate_u8, axis=-1))
        ),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = decode_frame()
    metrics: dict[str, object] = {
        "input": str(INPUT),
        "input_codec": "12-bit ProRes RAW decoded by AVFoundation to extended-linear BT.2020 float32",
        "frame": FRAME_INDEX,
        "test_dimensions": [TEST_WIDTH, TEST_HEIGHT],
        "exposure_stops": EXPOSURE_STOPS,
        "exposure": exposure_metrics(raw),
        "baseline_shoulder_samples_loge_0_0p5_1": BASELINE_CURVES[:, 9:12].tolist(),
        "candidate_shoulder_samples_loge_0_0p5_1": CANDIDATE_CURVES[:, 9:12].tolist(),
        "candidate_interpretation": "diagnostic lower bound: density held at the published logE=0 endpoint; not a proposed physical 5279 curve",
        "controlled_variables": "Only SENSITO_DENSITY_RGB at logE +0.5 and +1.0 differs; random seed and all decode, grain, DIR, print, scan and finishing parameters are identical.",
        "branches": {},
    }
    for look, name in (
        ("2383_projection_monitor", "projection"),
        ("cineon_bluray", "scan"),
    ):
        baseline = render(raw, BASELINE_CURVES, look)
        candidate = render(raw, CANDIDATE_CURVES, look)
        metrics["branches"][name] = compare(name, baseline, candidate)
    (OUTPUT / "shoulder_ab_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
