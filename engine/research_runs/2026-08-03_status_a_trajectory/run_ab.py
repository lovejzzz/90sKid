"""Controlled 2383 neutral-trajectory test for the V21 projection branch.

This research-only script compares four interpretations while leaving the RAW
decode, 5279 formation, stochastic seed, spectral print path, H-61 colour guard,
projection viewing adaptation and scan branch fixed:

1. V21's equal 1.00 Status-A LAD aim plus equal-density shaper.
2. Kodak's 1.09/1.06/1.03 aim plus the same equal-density shaper.
3. Kodak's aim plus a channel-independent analytical-dye-amount trajectory.
4. Kodak's aim with no additional print-density shaper.

The analytical-dye transform is the 2383 example published in Eastman Kodak's
US20020163657A1, paragraph 46.  Treating its three LAD-normalized dye amounts
as a common neutral scale is a model inference, not a disclosed 5279/2383 lab
measurement.
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


OUTPUT = Path(__file__).resolve().parent
INPUT = Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV")
DECODER = Path("/tmp/prores_raw_float_decode")
FRAME_INDEX = 12
SOURCE_WIDTH = 5760
SOURCE_HEIGHT = 4320
TEST_WIDTH = 1440
TEST_HEIGHT = 1080
EXPOSURE_STOPS = 0.45

V21_AIM = np.array([1.00, 1.00, 1.00], dtype=np.float32)
KODAK_AIM = np.array([1.09, 1.06, 1.03], dtype=np.float32)
STATUS_A_TO_ANALYTICAL_DYE = np.array(
    [
        [0.3260, -0.0402, -0.0287],
        [-0.3380, 0.3859, 0.3166],
        [-0.0017, -0.0361, 0.3677],
    ],
    dtype=np.float64,
)
ANALYTICAL_DYE_TO_STATUS_A = np.linalg.inv(STATUS_A_TO_ANALYTICAL_DYE)
LAD_ANALYTICAL_DYE = STATUS_A_TO_ANALYTICAL_DYE @ KODAK_AIM.astype(np.float64)

ORIGINAL_RAW_PRINT = emulsion._raw_print_2383_density_from_negative
ORIGINAL_PRINT_DENSITY = emulsion.print_2383_density_from_negative


def raw_print_with_aim(
    negative_density_rgb: np.ndarray, aim_rgb: np.ndarray
) -> np.ndarray:
    neutral_negative = emulsion.negative_total_printer_density(
        np.array([0.18, 0.18, 0.18], dtype=np.float32)
    )
    aim_log_exposure = np.array(
        [
            emulsion._inverse_2383_density(channel, float(aim_rgb[channel]))
            for channel in range(3)
        ],
        dtype=np.float32,
    )
    printer_log_light = neutral_negative + aim_log_exposure
    print_log_exposure = printer_log_light - negative_density_rgb
    density = np.empty_like(print_log_exposure, dtype=np.float32)
    for channel in range(3):
        density[..., channel] = np.interp(
            print_log_exposure[..., channel],
            emulsion.PRINT_2383_LOG_EXPOSURE,
            emulsion.PRINT_2383_DENSITY_RGB[channel],
        ).astype(np.float32)
    return density


def reset_caches() -> None:
    emulsion._PRINT_2383_NEUTRAL_SHAPERS = None
    emulsion._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    emulsion._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    emulsion._PRINT_2383_MONITOR_DELTA_LUT = None


def build_analytical_dye_shapers() -> tuple[list[np.ndarray], list[np.ndarray]]:
    stops = np.linspace(-12.0, 9.0, 337, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    raw = emulsion._raw_print_2383_density_from_negative(
        emulsion.negative_total_printer_density(neutral)
    ).astype(np.float64)
    analytical_dye = raw @ STATUS_A_TO_ANALYTICAL_DYE.T
    normalized_amounts = analytical_dye / LAD_ANALYTICAL_DYE[None, :]
    common_amount = np.mean(normalized_amounts, axis=1)
    target_ad = common_amount[:, None] * LAD_ANALYTICAL_DYE[None, :]
    target_status_a = target_ad @ ANALYTICAL_DYE_TO_STATUS_A.T

    x_tables: list[np.ndarray] = []
    y_tables: list[np.ndarray] = []
    for channel in range(3):
        order = np.argsort(raw[:, channel])
        x = raw[order, channel]
        y = target_status_a[order, channel]
        x, unique_indices = np.unique(x, return_index=True)
        y = y[unique_indices]
        x_tables.append(x.astype(np.float32))
        y_tables.append(y.astype(np.float32))
    return x_tables, y_tables


def analytical_dye_print_density(negative_density_rgb: np.ndarray) -> np.ndarray:
    if emulsion._PRINT_2383_NEUTRAL_SHAPERS is None:
        emulsion._PRINT_2383_NEUTRAL_SHAPERS = build_analytical_dye_shapers()
    raw = emulsion._raw_print_2383_density_from_negative(negative_density_rgb)
    x_tables, y_tables = emulsion._PRINT_2383_NEUTRAL_SHAPERS
    calibrated = np.empty_like(raw)
    for channel in range(3):
        calibrated[..., channel] = np.interp(
            raw[..., channel], x_tables[channel], y_tables[channel]
        ).astype(np.float32)
    return calibrated


def unshaped_print_density(negative_density_rgb: np.ndarray) -> np.ndarray:
    return emulsion._raw_print_2383_density_from_negative(negative_density_rgb)


MODES = {
    "v21_equal": (V21_AIM, ORIGINAL_PRINT_DENSITY),
    "kodak_equal": (KODAK_AIM, ORIGINAL_PRINT_DENSITY),
    "kodak_analytical_dye": (KODAK_AIM, analytical_dye_print_density),
    "kodak_unshaped": (KODAK_AIM, unshaped_print_density),
}


def set_mode(mode: str) -> None:
    aim, shaper = MODES[mode]
    emulsion._raw_print_2383_density_from_negative = (
        lambda negative_density_rgb: raw_print_with_aim(negative_density_rgb, aim)
    )
    emulsion.print_2383_density_from_negative = shaper
    reset_caches()


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


def render(raw: np.ndarray, mode: str, look: str) -> np.ndarray:
    set_mode(mode)
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


def to_srgb_u8(bt709: np.ndarray) -> np.ndarray:
    srgb = emulsion.srgb_encode(emulsion.bt709_decode(bt709))
    return np.rint(np.clip(srgb, 0.0, 1.0) * 255.0).astype(np.uint8)


def save_rgb(path: Path, image: np.ndarray) -> None:
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def compare(
    name: str, baseline: np.ndarray, candidate: np.ndarray
) -> dict[str, float]:
    baseline_linear = emulsion.bt709_decode(baseline)
    candidate_linear = emulsion.bt709_decode(candidate)
    delta = candidate_linear - baseline_linear
    baseline_lab = emulsion.linear_rec709_to_oklab(np.maximum(baseline_linear, 0.0))
    candidate_lab = emulsion.linear_rec709_to_oklab(np.maximum(candidate_linear, 0.0))
    delta_e = np.linalg.norm(candidate_lab - baseline_lab, axis=-1)
    baseline_luma = np.einsum(
        "...c,c->...", baseline_linear, [0.2126, 0.7152, 0.0722]
    )
    candidate_luma = np.einsum(
        "...c,c->...", candidate_linear, [0.2126, 0.7152, 0.0722]
    )
    mse = float(np.mean(np.square(delta)))
    baseline_u8 = to_srgb_u8(baseline)
    candidate_u8 = to_srgb_u8(candidate)
    save_rgb(OUTPUT / f"candidate_{name}.png", candidate_u8)
    save_rgb(
        OUTPUT / f"ab_{name}.png",
        np.concatenate([baseline_u8, candidate_u8], axis=1),
    )
    save_rgb(
        OUTPUT / f"difference_x12_{name}.png",
        np.rint(np.clip(0.5 + 12.0 * delta, 0.0, 1.0) * 255.0).astype(np.uint8),
    )
    return {
        "linear_rgb_mae": float(np.mean(np.abs(delta))),
        "linear_rgb_max_abs": float(np.max(np.abs(delta))),
        "psnr_db": float("inf") if mse == 0.0 else float(-10.0 * np.log10(mse)),
        "oklab_delta_e_median": float(np.median(delta_e)),
        "oklab_delta_e_p95": float(np.percentile(delta_e, 95)),
        "oklab_delta_e_p99": float(np.percentile(delta_e, 99)),
        "luma_delta_p95_abs": float(np.percentile(np.abs(candidate_luma - baseline_luma), 95)),
        "baseline_luma_p1": float(np.percentile(baseline_luma, 1)),
        "candidate_luma_p1": float(np.percentile(candidate_luma, 1)),
        "baseline_luma_p99": float(np.percentile(baseline_luma, 99)),
        "candidate_luma_p99": float(np.percentile(candidate_luma, 99)),
        "candidate_clip_low_percent": float(100.0 * np.mean(candidate_linear <= 0.0)),
        "candidate_clip_high_percent": float(100.0 * np.mean(candidate_linear >= 1.0)),
        "eight_bit_pixels_changed_percent": float(
            100.0 * np.mean(np.any(baseline_u8 != candidate_u8, axis=-1))
        ),
    }


def status_a_to_normalized_ad(status_a: np.ndarray) -> np.ndarray:
    analytical_dye = np.asarray(status_a, dtype=np.float64) @ STATUS_A_TO_ANALYTICAL_DYE.T
    return analytical_dye / LAD_ANALYTICAL_DYE


def neutral_scale_metrics(mode: str) -> dict[str, object]:
    set_mode(mode)
    probe_stops = np.array([-3.0, -2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)
    levels = 0.18 * np.power(2.0, probe_stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    negative = emulsion.negative_total_printer_density(neutral)
    raw = emulsion._raw_print_2383_density_from_negative(negative)
    shaped = emulsion.print_2383_density_from_negative(negative)
    normalized_ad = status_a_to_normalized_ad(shaped)
    ad_spans = np.ptp(normalized_ad, axis=1)

    lad_negative = emulsion.negative_total_printer_density(
        np.array([0.18, 0.18, 0.18], dtype=np.float32)
    )
    lad_raw = emulsion._raw_print_2383_density_from_negative(lad_negative)
    lad_shaped = emulsion.print_2383_density_from_negative(lad_negative)
    return {
        "probe_note": "Six representative stops, not measured H-61 patch exposures.",
        "probe_stops_from_18_percent": probe_stops.astype(float).tolist(),
        "raw_status_a": raw.astype(float).tolist(),
        "shaped_status_a": shaped.astype(float).tolist(),
        "lad_raw_status_a": np.asarray(lad_raw).astype(float).tolist(),
        "lad_shaped_status_a": np.asarray(lad_shaped).astype(float).tolist(),
        "lad_shaped_rms_error_from_kodak_aim": float(
            np.sqrt(np.mean(np.square(lad_shaped - KODAK_AIM)))
        ),
        "lad_normalized_analytical_dye": status_a_to_normalized_ad(lad_shaped).astype(float).tolist(),
        "six_probe_normalized_analytical_dye": normalized_ad.astype(float).tolist(),
        "six_probe_ad_channel_span": ad_spans.astype(float).tolist(),
        "six_probe_ad_channel_span_mean": float(np.mean(ad_spans)),
        "six_probe_ad_channel_span_max": float(np.max(ad_spans)),
    }


def patch_metrics(mode: str) -> dict[str, object]:
    set_mode(mode)
    values = np.array(
        [
            [0.18, 0.18, 0.18],
            [0.18, 0.01, 0.01], [0.01, 0.18, 0.01], [0.01, 0.01, 0.18],
            [0.18, 0.18, 0.01], [0.18, 0.01, 0.18], [0.01, 0.18, 0.18],
        ],
        dtype=np.float32,
    )
    names = ("neutral", "red", "green", "blue", "yellow", "magenta", "cyan")
    raster = values[None, ...]
    projection = emulsion.render_to_display_linear(
        raster,
        exposure_stops=0.0,
        include_optical_scatter=False,
        look="2383_projection_monitor",
        raw_colour="panasonic_official",
        sensor_noise_treatment="preserve",
    )[0]
    scan = emulsion.render_to_display_linear(
        raster,
        exposure_stops=0.0,
        include_optical_scatter=False,
        look="cineon_bluray",
        raw_colour="panasonic_official",
        sensor_noise_treatment="preserve",
    )[0]
    projection_lab = emulsion.linear_rec709_to_oklab(np.maximum(projection, 0.0))
    scan_lab = emulsion.linear_rec709_to_oklab(np.maximum(scan, 0.0))
    delta_e = np.linalg.norm(projection_lab - scan_lab, axis=-1)
    hue_delta = np.degrees(
        np.arctan2(projection_lab[:, 2], projection_lab[:, 1])
        - np.arctan2(scan_lab[:, 2], scan_lab[:, 1])
    )
    hue_delta = np.abs((hue_delta + 180.0) % 360.0 - 180.0)
    return {
        "patch_order": list(names),
        "projection_linear_rgb": projection.astype(float).tolist(),
        "scan_linear_rgb": scan.astype(float).tolist(),
        "projection_scan_oklab_delta_e": delta_e.astype(float).tolist(),
        "projection_scan_absolute_hue_delta_degrees": hue_delta.astype(float).tolist(),
        "mean_colour_delta_e_excluding_neutral": float(np.mean(delta_e[1:])),
        "mean_absolute_hue_delta_degrees_excluding_neutral": float(np.mean(hue_delta[1:])),
        "neutral_projection_rgb_span": float(np.ptp(projection[0])),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = decode_frame()

    renders: dict[str, np.ndarray] = {}
    for mode in MODES:
        renders[mode] = render(raw, mode, "2383_projection_monitor")
    set_mode("v21_equal")
    baseline_scan = render(raw, "v21_equal", "cineon_bluray")
    candidate_scan = render(raw, "kodak_analytical_dye", "cineon_bluray")

    baseline_u8 = to_srgb_u8(renders["v21_equal"])
    save_rgb(OUTPUT / "baseline_v21_equal.png", baseline_u8)

    result = {
        "question": "Which bounded 2383 neutral Status-A trajectory can preserve Kodak's 1.09/1.06/1.03 LAD vector without inventing fixed offsets?",
        "input": str(INPUT),
        "decode": "12-bit ProRes RAW via AVFoundation extended-linear BT.2020 float32",
        "frame": FRAME_INDEX,
        "dimensions": [TEST_WIDTH, TEST_HEIGHT],
        "exposure_stops": EXPOSURE_STOPS,
        "seed_policy": "V21 deterministic frame-index seed; identical for every variant",
        "status_a_to_analytical_dye_matrix": STATUS_A_TO_ANALYTICAL_DYE.astype(float).tolist(),
        "matrix_source": "Eastman Kodak US20020163657A1 paragraph 46, 2383 example",
        "model_boundary": "Using LAD-normalized analytical dye amounts as a common neutral trajectory is an inference; no measured 5279-to-2383 six-step target is available.",
        "controlled_variables": "Only the 2383 printer-light LAD aim and print-density neutral shaper vary. RAW decode, +0.45 stop, 5279 H-D/chemistry/DIR/morphology/seed, spectral printing density, 3200 K lamp, 2383 curves/dyes, Callier term, xenon projection, H-61 colour guard, monitor adaptation and scan branch remain fixed.",
        "neutral_scale_gate": {mode: neutral_scale_metrics(mode) for mode in MODES},
        "patch_gate": {mode: patch_metrics(mode) for mode in MODES},
        "frame_ab_vs_v21": {
            mode: compare(mode, renders["v21_equal"], renders[mode])
            for mode in MODES if mode != "v21_equal"
        },
        "scan_branch_isolation": compare(
            "scan_isolation", baseline_scan, candidate_scan
        ),
    }
    (OUTPUT / "metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    emulsion._raw_print_2383_density_from_negative = ORIGINAL_RAW_PRINT
    emulsion.print_2383_density_from_negative = ORIGINAL_PRINT_DENSITY
    reset_caches()


if __name__ == "__main__":
    main()
