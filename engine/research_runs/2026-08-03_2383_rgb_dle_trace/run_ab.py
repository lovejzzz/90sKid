"""Research-only three-channel trace of the Kodak 2383 neutral DLE series.

The preceding run could read the green dashed curve in US6987586B2 Figure 3
but retained only the midpoint of the nearly overlapping red solid and blue
dotted curves.  This run follows the red curve's continuous connected path and
reflects the recorded red/blue midpoint around that path to recover blue.  The
even patent steps 2/4/6/8 fit a bounded RGB departure curve; odd steps 3/5/7
remain blind.  Production code is never modified.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from scipy.signal import medfilt, savgol_filter


ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT = ROOT / "experiments" / "emulsion_reconstruction"
sys.path.insert(0, str(EXPERIMENT / "src"))
import emulsion_experiment as emulsion


PREVIOUS_SCRIPT = (
    EXPERIMENT
    / "research_runs"
    / "2026-08-03_2383_dle_holdout"
    / "run_ab.py"
)
spec = importlib.util.spec_from_file_location("dle_green_holdout", PREVIOUS_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {PREVIOUS_SCRIPT}")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
status_run = previous.status_run


OUTPUT = Path(__file__).resolve().parent
previous.OUTPUT = OUTPUT
previous.previous.OUTPUT = OUTPUT
status_run.OUTPUT = OUTPUT

ARCHIVED_SHEET_URL = (
    "https://www.archives.gov/files/preservation/products/resources/2383-TI.pdf"
)
ARCHIVED_SHEET_SHA256 = (
    "76b692f08eac97fa46ae89d7229fe5f854a958827f4faba78405af204dfe0156"
)
ARCHIVED_SHEET_NOTE = (
    "Kodak H-1-2383t, revised March 2005; PDF metadata CreationDate 1997-12-05; "
    "page 5 vector sensitometric curves F002_1254AC"
)

PATCH_STEPS = previous.PATCH_STEPS.copy()
TRAIN_STEPS = previous.TRAIN_STEPS.copy()
HOLDOUT_STEPS = previous.HOLDOUT_STEPS.copy()
FIGURE_PATH = previous.FIGURE_PATH
EXPECTED_RED_X = np.array(
    [259.75, 301.59, 372.33, 505.76, 703.86, 957.20, 1185.75],
    dtype=np.float64,
)
SELECTED_FRAMES = (120, 144, 164)
FRAME_SELECTION_NOTE = (
    "Frames selected from a 15-frame sparse RAW inventory. Frame 120 had the "
    "largest fraction above mean 2383 Status-A density 2.5 (49.3004%); frame "
    "144 had the largest mean density (2.37611 D); frame 164 had the largest "
    "fraction above 3.0 D (28.3570%)."
)

ORIGINAL_RAW_PRINT = emulsion._raw_print_2383_density_from_negative
ORIGINAL_PRINT_DENSITY = emulsion.print_2383_density_from_negative
ORIGINAL_VIEW_NEUTRALIZER = emulsion.neutralize_2383_projected_gray_scale
KODAK_AIM = status_run.KODAK_AIM.astype(np.float64)
LAD_MEAN = float(np.mean(KODAK_AIM))
LUMA_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)

_RGB_SHAPERS: tuple[list[np.ndarray], list[np.ndarray]] | None = None
_RGB_VIEW_TABLE: tuple[np.ndarray, np.ndarray] | None = None


def trace_red_curve_x() -> tuple[np.ndarray, list[dict[str, float]]]:
    """Trace the patent's continuous red solid curve without manual line picks."""
    image = cv2.imread(str(FIGURE_PATH), cv2.IMREAD_GRAYSCALE)
    if image is None or image.shape != (2781, 2082):
        raise RuntimeError(f"unexpected patent figure: {None if image is None else image.shape}")
    binary = (image < 128).astype(np.uint8)
    _, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)

    # The solid curve joins the graph boundary at D-min and is therefore part
    # of the large plot component containing the seed at patent step 2.
    seed_component = int(labels[2059, 260])
    if seed_component == 0:
        raise RuntimeError("red trace seed missed the plot component")

    y_axis = np.arange(1300, 2120)
    rough_x = np.interp(
        y_axis,
        [1440, 1543, 1646, 1750, 1853, 1956, 2059],
        previous.RB_MIDPOINT_X[::-1],
    )
    row_centres: list[float] = []
    x_coordinates = np.arange(image.shape[1])
    for y, rough in zip(y_axis, rough_x):
        x = np.where(
            (labels[y] == seed_component) & (np.abs(x_coordinates - rough) < 80)
        )[0]
        row_centres.append(float(np.median(x)) if x.size else np.nan)
    row_centres_array = np.asarray(row_centres, dtype=np.float64)
    valid = np.isfinite(row_centres_array)
    row_centres_array = np.interp(
        y_axis, y_axis[valid], row_centres_array[valid]
    )
    smooth = savgol_filter(medfilt(row_centres_array, 31), 101, 3)
    patch_y = 2162.0 - (PATCH_STEPS.astype(np.float64) - 1.0) * 103.1
    red_x = np.interp(patch_y, y_axis, smooth)
    if float(np.max(np.abs(red_x - EXPECTED_RED_X))) > 0.35:
        raise RuntimeError(f"red trace drifted: {red_x.tolist()}")

    # Independently retained blue-dot components verify that the dotted path
    # crosses from the low-density side of red to the high-density side.
    isolated_blue_dots: list[dict[str, float]] = []
    for index in range(1, len(stats)):
        x, y, width, height, area = stats[index]
        centre_x, centre_y = centroids[index]
        if not (
            1300 <= centre_y <= 2120
            and 180 <= centre_x <= 1300
            and 25 <= area <= 65
            and 5 <= width <= 11
            and 5 <= height <= 10
        ):
            continue
        red_at_y = float(np.interp(centre_y, y_axis, smooth))
        if abs(centre_x - red_at_y) <= 35:
            isolated_blue_dots.append(
                {
                    "x": float(centre_x),
                    "y": float(centre_y),
                    "x_minus_red": float(centre_x - red_at_y),
                }
            )
    return red_x, isolated_blue_dots


RED_X, BLUE_DOT_CHECKS = trace_red_curve_x()
BLUE_X = 2.0 * previous.RB_MIDPOINT_X - RED_X
GREEN_X = previous.GREEN_X.copy()
TARGET_STATUS_A = previous.pixel_to_density(
    np.stack([RED_X, GREEN_X, BLUE_X], axis=1)
)
TARGET_MEAN_DENSITY = np.mean(TARGET_STATUS_A, axis=1)
TARGET_DEPARTURE = TARGET_STATUS_A - TARGET_MEAN_DENSITY[:, None]
TRAIN_MASK = np.array([int(step) in TRAIN_STEPS for step in PATCH_STEPS])
HOLDOUT_MASK = np.array([int(step) in HOLDOUT_STEPS for step in PATCH_STEPS])


def training_departure_curve() -> tuple[np.ndarray, np.ndarray]:
    means = [0.03, LAD_MEAN]
    departures = [np.zeros(3), KODAK_AIM - LAD_MEAN]
    for mean, departure, keep in zip(
        TARGET_MEAN_DENSITY, TARGET_DEPARTURE, TRAIN_MASK
    ):
        if bool(keep):
            means.append(float(mean))
            departures.append(departure)
    means.append(4.15)
    departures.append(np.zeros(3))
    order = np.argsort(means)
    return np.asarray(means)[order], np.asarray(departures)[order]


TRAIN_MEAN_DENSITY, TRAIN_DEPARTURE = training_departure_curve()


def target_rgb_departure(mean_density: np.ndarray) -> np.ndarray:
    mean = np.asarray(mean_density, dtype=np.float64)
    return np.stack(
        [
            np.interp(
                mean,
                TRAIN_MEAN_DENSITY,
                TRAIN_DEPARTURE[:, channel],
                left=0.0,
                right=0.0,
            )
            for channel in range(3)
        ],
        axis=-1,
    )


def apply_rgb_departure(status_a: np.ndarray) -> np.ndarray:
    target = np.asarray(status_a, dtype=np.float64).copy()
    mean = np.mean(target, axis=-1)
    current_departure = target - mean[..., None]
    target += target_rgb_departure(mean) - current_departure
    return np.clip(target, 0.0, emulsion.PRINT_2383_DMAX).astype(np.float32)


def reset_caches() -> None:
    global _RGB_SHAPERS, _RGB_VIEW_TABLE
    status_run.reset_caches()
    previous._DLE_SHAPERS = None
    previous._DLE_VIEW_TABLE = None
    _RGB_SHAPERS = None
    _RGB_VIEW_TABLE = None


def build_rgb_shapers() -> tuple[list[np.ndarray], list[np.ndarray]]:
    stops = np.linspace(-12.0, 9.0, 337, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    raw = emulsion._raw_print_2383_density_from_negative(
        emulsion.negative_total_printer_density(neutral)
    ).astype(np.float64)
    analytical_dye = raw @ status_run.STATUS_A_TO_ANALYTICAL_DYE.T
    normalized = analytical_dye / status_run.LAD_ANALYTICAL_DYE[None, :]
    common_amount = np.mean(normalized, axis=1)
    target_ad = common_amount[:, None] * status_run.LAD_ANALYTICAL_DYE[None, :]
    proportional = target_ad @ status_run.ANALYTICAL_DYE_TO_STATUS_A.T
    target = apply_rgb_departure(proportional)

    x_tables: list[np.ndarray] = []
    y_tables: list[np.ndarray] = []
    for channel in range(3):
        order = np.argsort(raw[:, channel])
        x = raw[order, channel]
        y = target[order, channel]
        x, unique_indices = np.unique(x, return_index=True)
        x_tables.append(x.astype(np.float32))
        y_tables.append(y[unique_indices].astype(np.float32))
    return x_tables, y_tables


def rgb_print_density(negative_density_rgb: np.ndarray) -> np.ndarray:
    global _RGB_SHAPERS
    if _RGB_SHAPERS is None:
        _RGB_SHAPERS = build_rgb_shapers()
    raw = emulsion._raw_print_2383_density_from_negative(negative_density_rgb)
    x_tables, y_tables = _RGB_SHAPERS
    calibrated = np.empty_like(raw)
    for channel in range(3):
        calibrated[..., channel] = np.interp(
            raw[..., channel], x_tables[channel], y_tables[channel]
        ).astype(np.float32)
    return calibrated


def build_rgb_view_table() -> tuple[np.ndarray, np.ndarray]:
    mean_density = np.linspace(0.0, emulsion.PRINT_2383_DMAX, 513)
    proportional = mean_density[:, None] * KODAK_AIM[None, :] / LAD_MEAN
    status_a = apply_rgb_departure(proportional)
    callier = emulsion.apply_2383_callier_density(status_a[None, ...])
    rgb = np.maximum(emulsion.apply_2383_projection_lut(callier)[0], 1e-8)
    luma = np.einsum("...c,c->...", rgb, LUMA_WEIGHTS)
    factors = luma[:, None] / rgb
    order = np.argsort(luma)
    return (
        luma[order].astype(np.float32),
        np.clip(factors[order], 0.35, 2.50).astype(np.float32),
    )


def rgb_view_neutralizer(projected: np.ndarray) -> np.ndarray:
    global _RGB_VIEW_TABLE
    if _RGB_VIEW_TABLE is None:
        _RGB_VIEW_TABLE = build_rgb_view_table()
    luma_axis, factor_table = _RGB_VIEW_TABLE
    source = np.maximum(np.asarray(projected, dtype=np.float32), 0.0)
    luma = np.einsum("...c,c->...", source, LUMA_WEIGHTS)
    corrected = np.empty_like(source)
    for channel in range(3):
        factor = np.interp(luma, luma_axis, factor_table[:, channel])
        corrected[..., channel] = source[..., channel] * factor
    return np.maximum(corrected, 0.0).astype(np.float32)


def set_mode(mode: str) -> None:
    if mode in ("v21_equal", "patent_dle_holdout"):
        previous.set_mode(mode)
        return
    if mode != "patent_rgb_holdout":
        raise KeyError(mode)
    emulsion._raw_print_2383_density_from_negative = (
        lambda negative_density_rgb: status_run.raw_print_with_aim(
            negative_density_rgb, status_run.KODAK_AIM
        )
    )
    emulsion.print_2383_density_from_negative = rgb_print_density
    emulsion.neutralize_2383_projected_gray_scale = rgb_view_neutralizer
    reset_caches()


def neutral_trajectory(mode: str) -> tuple[np.ndarray, np.ndarray]:
    set_mode(mode)
    stops = np.linspace(-12.0, 9.0, 337, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    negative = emulsion.negative_total_printer_density(neutral)
    shaped = emulsion.print_2383_density_from_negative(negative).astype(np.float64)
    mean = np.mean(shaped, axis=1)
    departure = shaped - mean[:, None]
    order = np.argsort(mean)
    return mean[order], departure[order]


def trajectory_gate(mode: str) -> dict[str, object]:
    mean_axis, departure_axis = neutral_trajectory(mode)
    predicted = np.stack(
        [
            np.interp(TARGET_MEAN_DENSITY, mean_axis, departure_axis[:, channel])
            for channel in range(3)
        ],
        axis=1,
    )
    error = predicted - TARGET_DEPARTURE
    return {
        "predicted_rgb_departure_from_mean_density": predicted.astype(float).tolist(),
        "error_rgb_density": error.astype(float).tolist(),
        "all_channel_all_point_rmse_density": float(np.sqrt(np.mean(np.square(error)))),
        "all_channel_training_rmse_density": float(
            np.sqrt(np.mean(np.square(error[TRAIN_MASK])))
        ),
        "all_channel_blind_holdout_rmse_density": float(
            np.sqrt(np.mean(np.square(error[HOLDOUT_MASK])))
        ),
        "blind_holdout_max_abs_error_density": float(
            np.max(np.abs(error[HOLDOUT_MASK]))
        ),
        "blind_holdout_channel_rmse_density": np.sqrt(
            np.mean(np.square(error[HOLDOUT_MASK]), axis=0)
        ).astype(float).tolist(),
    }


def view_gate(mode: str) -> dict[str, object]:
    set_mode(mode)
    probe_stops = np.array([-3.0, -2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)
    levels = 0.18 * np.power(2.0, probe_stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    negative = emulsion.negative_total_printer_density(neutral)
    status_a = emulsion.print_2383_density_from_negative(negative)
    callier = emulsion.apply_2383_callier_density(status_a[None, ...])
    spectral = np.maximum(emulsion.apply_2383_projection_lut(callier)[0], 0.0)
    corrected = emulsion.neutralize_2383_projected_gray_scale(spectral)
    lab = emulsion.linear_rec709_to_oklab(corrected[None, ...])[0]
    chroma = np.linalg.norm(lab[:, 1:3], axis=1)
    return {
        "probe_note": "Representative neutral stops; not patent patch numbers.",
        "probe_stops_from_18_percent": probe_stops.astype(float).tolist(),
        "status_a": status_a.astype(float).tolist(),
        "corrected_oklab_chroma": chroma.astype(float).tolist(),
        "corrected_oklab_chroma_mean": float(np.mean(chroma)),
        "corrected_oklab_chroma_max": float(np.max(chroma)),
    }


def decode_frame(frame_index: int) -> np.ndarray:
    expected = status_run.SOURCE_WIDTH * status_run.SOURCE_HEIGHT * 3 * 4
    result = subprocess.run(
        [str(status_run.DECODER), str(status_run.INPUT), str(frame_index), "1"],
        check=True,
        stdout=subprocess.PIPE,
    )
    if len(result.stdout) != expected:
        raise RuntimeError(f"decoder returned {len(result.stdout)} bytes, expected {expected}")
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(
        status_run.SOURCE_HEIGHT, status_run.SOURCE_WIDTH, 3
    )
    return cv2.resize(
        raw,
        (status_run.TEST_WIDTH, status_run.TEST_HEIGHT),
        interpolation=cv2.INTER_AREA,
    )


def render(raw: np.ndarray, frame_index: int, mode: str, look: str) -> np.ndarray:
    set_mode(mode)
    return emulsion.reconstruct_through_emulsion(
        raw,
        frame_index,
        grain_scale=1.0,
        oversample=1,
        exposure_stops=status_run.EXPOSURE_STOPS,
        look=look,
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )


def compare(
    name: str,
    baseline: np.ndarray,
    candidate: np.ndarray,
    save_images: bool = True,
) -> dict[str, float]:
    baseline_linear = emulsion.bt709_decode(baseline)
    candidate_linear = emulsion.bt709_decode(candidate)
    delta = candidate_linear - baseline_linear
    baseline_lab = emulsion.linear_rec709_to_oklab(np.maximum(baseline_linear, 0.0))
    candidate_lab = emulsion.linear_rec709_to_oklab(np.maximum(candidate_linear, 0.0))
    delta_e = np.linalg.norm(candidate_lab - baseline_lab, axis=-1)
    baseline_luma = np.einsum("...c,c->...", baseline_linear, LUMA_WEIGHTS)
    candidate_luma = np.einsum("...c,c->...", candidate_linear, LUMA_WEIGHTS)
    mse = float(np.mean(np.square(delta)))
    baseline_u8 = status_run.to_srgb_u8(baseline)
    candidate_u8 = status_run.to_srgb_u8(candidate)
    if save_images:
        status_run.save_rgb(OUTPUT / f"baseline_{name}.png", baseline_u8)
        status_run.save_rgb(OUTPUT / f"candidate_{name}.png", candidate_u8)
        status_run.save_rgb(
            OUTPUT / f"ab_{name}.png",
            np.concatenate([baseline_u8, candidate_u8], axis=1),
        )
        status_run.save_rgb(
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
        "luma_delta_p95_abs": float(
            np.percentile(np.abs(candidate_luma - baseline_luma), 95)
        ),
        "baseline_luma_p1": float(np.percentile(baseline_luma, 1)),
        "candidate_luma_p1": float(np.percentile(candidate_luma, 1)),
        "baseline_luma_p99": float(np.percentile(baseline_luma, 99)),
        "candidate_luma_p99": float(np.percentile(candidate_luma, 99)),
        "candidate_clip_low_percent": float(100.0 * np.mean(candidate_linear <= 0.0)),
        "candidate_clip_high_percent": float(100.0 * np.mean(candidate_linear >= 1.0)),
        "baseline_exact_black_pixel_percent_8bit": float(
            100.0 * np.mean(np.all(baseline_u8 == 0, axis=-1))
        ),
        "candidate_exact_black_pixel_percent_8bit": float(
            100.0 * np.mean(np.all(candidate_u8 == 0, axis=-1))
        ),
        "eight_bit_pixels_changed_percent": float(
            100.0 * np.mean(np.any(baseline_u8 != candidate_u8, axis=-1))
        ),
    }


def save_digitization() -> None:
    with (OUTPUT / "digitized_dle_rgb.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "patch_step",
                "role",
                "red_x_px",
                "green_x_px",
                "blue_x_px",
                "red_status_a_density",
                "green_status_a_density",
                "blue_status_a_density",
                "mean_status_a_density",
                "single_curve_reading_uncertainty_density",
            ]
        )
        for step, red_x, green_x, blue_x, density in zip(
            PATCH_STEPS, RED_X, GREEN_X, BLUE_X, TARGET_STATUS_A
        ):
            writer.writerow(
                [
                    int(step),
                    "training" if int(step) in TRAIN_STEPS else "blind_holdout",
                    red_x,
                    green_x,
                    blue_x,
                    *density.astype(float).tolist(),
                    float(np.mean(density)),
                    previous.DENSITY_UNCERTAINTY,
                ]
            )


def json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return "infinite (bit-identical)"
    return value


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    previous.ensure_source_figure()
    save_digitization()

    trajectory_gates = {
        mode: trajectory_gate(mode)
        for mode in ("v21_equal", "patent_dle_holdout", "patent_rgb_holdout")
    }
    frame_results: dict[str, object] = {}
    for frame_index in SELECTED_FRAMES:
        raw = decode_frame(frame_index)
        baseline = render(raw, frame_index, "v21_equal", "2383_projection_monitor")
        candidate = render(
            raw, frame_index, "patent_rgb_holdout", "2383_projection_monitor"
        )
        frame_results[str(frame_index)] = compare(
            f"rgb_dle_frame{frame_index}", baseline, candidate
        )
        if frame_index == 144:
            green_only = render(
                raw, frame_index, "patent_dle_holdout", "2383_projection_monitor"
            )
            frame_results[str(frame_index)]["rgb_vs_green_only"] = compare(
                "rgb_vs_green_only_frame144", green_only, candidate
            )
            baseline_scan = render(raw, frame_index, "v21_equal", "cineon_bluray")
            candidate_scan = render(
                raw, frame_index, "patent_rgb_holdout", "cineon_bluray"
            )
            frame_results[str(frame_index)]["scan_branch_isolation"] = compare(
                "scan_isolation_frame144", baseline_scan, candidate_scan
            )

    result = {
        "question": "Can the patent's red solid and blue dotted 2383 DLE traces be separated reproducibly, and does a full-RGB neutral trajectory improve blind holdout and multi-frame RAW behavior over the prior green-only candidate?",
        "sources": {
            "patent": {
                "url": previous.FIGURE_URL,
                "sha256": previous.FIGURE_SHA256,
                "description": "US6987586B2 Figure 3, Kodak VISION 2383 control-neutral DLE series",
            },
            "archived_data_sheet": {
                "url": ARCHIVED_SHEET_URL,
                "sha256": ARCHIVED_SHEET_SHA256,
                "description": ARCHIVED_SHEET_NOTE,
            },
        },
        "input": str(status_run.INPUT),
        "decode": "12-bit ProRes RAW via AVFoundation extended-linear BT.2020 float32",
        "selected_frames": list(SELECTED_FRAMES),
        "frame_selection": FRAME_SELECTION_NOTE,
        "dimensions": [status_run.TEST_WIDTH, status_run.TEST_HEIGHT],
        "exposure_stops": status_run.EXPOSURE_STOPS,
        "seed_policy": "V21 deterministic frame-index seed; identical within every A/B pair",
        "digitization": {
            "method": "Continuous red path from the patent raster's seeded plot component, 31-row median plus 101-row cubic Savitzky-Golay smoothing; blue reflected from the previous red/blue midpoint; green unchanged.",
            "red_x_px": RED_X.astype(float).tolist(),
            "green_x_px": GREEN_X.astype(float).tolist(),
            "blue_x_px": BLUE_X.astype(float).tolist(),
            "target_status_a_rgb_density": TARGET_STATUS_A.astype(float).tolist(),
            "target_rgb_departure_from_mean_density": TARGET_DEPARTURE.astype(float).tolist(),
            "single_curve_reading_uncertainty_density": previous.DENSITY_UNCERTAINTY,
            "isolated_blue_dot_checks": BLUE_DOT_CHECKS,
        },
        "controlled_variables": "Only the 2383 neutral Status-A shaper and its matching post-spectral neutral table change. RAW decode, +0.45-stop exposure, 5279 H-D/chemistry/DIR/morphology/seed, 3200 K printer model, 2383 base curves/dyes, Callier term, xenon SPD, H-61 colour guard, monitor adaptation, grain and scan branch remain fixed.",
        "trajectory_gate": trajectory_gates,
        "view_gate": {
            mode: view_gate(mode)
            for mode in ("v21_equal", "patent_dle_holdout", "patent_rgb_holdout")
        },
        "patch_gate": {
            mode: (
                set_mode(mode), previous.previous._patch_gate_current()
            )[1]
            for mode in ("v21_equal", "patent_dle_holdout", "patent_rgb_holdout")
        },
        "multi_frame_ab_vs_v21": frame_results,
    }

    (OUTPUT / "metrics.json").write_text(
        json.dumps(json_safe(result), ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )

    emulsion._raw_print_2383_density_from_negative = ORIGINAL_RAW_PRINT
    emulsion.print_2383_density_from_negative = ORIGINAL_PRINT_DENSITY
    emulsion.neutralize_2383_projected_gray_scale = ORIGINAL_VIEW_NEUTRALIZER
    reset_caches()


if __name__ == "__main__":
    main()
