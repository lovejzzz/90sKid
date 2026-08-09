"""Independent 2383 DLE neutral-crossover holdout experiment.

US6987586B2 Figure 3 identifies its plotted curves as the Kodak VISION 2383
control-neutral Density Log Exposure (DLE) series.  This script digitizes the
clearly separated green curve relative to the red/blue midpoint.  Even-numbered
patches 2/4/6/8 define a restrained correction; odd-numbered patches 3/5/7 are
kept blind as holdouts.

The candidate is research-only.  It retains the official 1.09/1.06/1.03 LAD
anchor and the preceding analytical-dye trajectory, adds only the measured
high-density green crossover, and calibrates the post-spectral neutral table on
that trajectory.  All 5279, RAW, grain, DIR, print-light, xenon, scan and
finishing parameters remain unchanged.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
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


PREVIOUS_SCRIPT = (
    EXPERIMENT
    / "research_runs"
    / "2026-08-03_projected_gray_anchor"
    / "run_ab.py"
)
spec = importlib.util.spec_from_file_location("projected_gray_anchor_ab", PREVIOUS_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {PREVIOUS_SCRIPT}")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
status_run = previous.previous


OUTPUT = Path(__file__).resolve().parent
previous.OUTPUT = OUTPUT
status_run.OUTPUT = OUTPUT

FIGURE_URL = (
    "https://patentimages.storage.googleapis.com/8e/97/7a/"
    "2d30a2e80dd75f/US06987586-20060117-D00003.png"
)
FIGURE_SHA256 = "9325994fead512abcc6f037d6915a533cf8993daae797bd9a255a9d72076574e"
FIGURE_PATH = OUTPUT / "US6987586B2_figure_3.png"

# Plot calibration read from the high-resolution patent figure.  The original
# page is rotated: density decreases left-to-right from 4.5 to 0.0.  The pixel
# picks are centres of the visible line strokes.  Red and blue nearly overlap,
# so only their midpoint is claimed; the separated dashed green curve is the
# falsifiable quantity.  A +/-4 pixel reading uncertainty is retained below.
PLOT_LEFT_X = 125.0
PLOT_RIGHT_X = 1563.0
PLOT_DENSITY_LEFT = 4.5
PLOT_DENSITY_RIGHT = 0.0
PIXEL_UNCERTAINTY = 4.0
PATCH_STEPS = np.array([2, 3, 4, 5, 6, 7, 8], dtype=np.int32)
RB_MIDPOINT_X = np.array([260.0, 306.0, 371.5, 505.0, 701.5, 945.5, 1180.0])
GREEN_X = np.array([280.0, 339.5, 442.0, 598.5, 789.5, 1012.0, 1199.5])
TRAIN_STEPS = {2, 4, 6, 8}
HOLDOUT_STEPS = {3, 5, 7}

ORIGINAL_RAW_PRINT = emulsion._raw_print_2383_density_from_negative
ORIGINAL_PRINT_DENSITY = emulsion.print_2383_density_from_negative
ORIGINAL_VIEW_NEUTRALIZER = emulsion.neutralize_2383_projected_gray_scale
KODAK_AIM = status_run.KODAK_AIM.astype(np.float64)
LAD_MEAN = float(np.mean(KODAK_AIM))
LUMA_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)

_DLE_SHAPERS: tuple[list[np.ndarray], list[np.ndarray]] | None = None
_DLE_VIEW_TABLE: tuple[np.ndarray, np.ndarray] | None = None


def ensure_source_figure() -> None:
    if not FIGURE_PATH.exists():
        subprocess.run(
            ["curl", "-L", "--fail", "--silent", "--show-error", FIGURE_URL, "-o", str(FIGURE_PATH)],
            check=True,
        )
    digest = hashlib.sha256(FIGURE_PATH.read_bytes()).hexdigest()
    if digest != FIGURE_SHA256:
        raise RuntimeError(f"Figure 3 hash mismatch: {digest}")
    image = cv2.imread(str(FIGURE_PATH), cv2.IMREAD_GRAYSCALE)
    if image is None or image.shape != (2781, 2082):
        raise RuntimeError(f"unexpected Figure 3 raster: {None if image is None else image.shape}")


def pixel_to_density(x: np.ndarray | float) -> np.ndarray:
    fraction = (np.asarray(x, dtype=np.float64) - PLOT_LEFT_X) / (
        PLOT_RIGHT_X - PLOT_LEFT_X
    )
    return PLOT_DENSITY_LEFT + fraction * (
        PLOT_DENSITY_RIGHT - PLOT_DENSITY_LEFT
    )


RB_DENSITY = pixel_to_density(RB_MIDPOINT_X)
GREEN_DENSITY = pixel_to_density(GREEN_X)
TARGET_MEAN_DENSITY = (2.0 * RB_DENSITY + GREEN_DENSITY) / 3.0
TARGET_GREEN_MINUS_RB = GREEN_DENSITY - RB_DENSITY
DENSITY_UNCERTAINTY = float(
    PIXEL_UNCERTAINTY
    * abs(PLOT_DENSITY_LEFT - PLOT_DENSITY_RIGHT)
    / abs(PLOT_RIGHT_X - PLOT_LEFT_X)
)


def reset_caches() -> None:
    global _DLE_SHAPERS, _DLE_VIEW_TABLE
    status_run.reset_caches()
    _DLE_SHAPERS = None
    _DLE_VIEW_TABLE = None


def _training_curve() -> tuple[np.ndarray, np.ndarray]:
    means = [0.03, LAD_MEAN]
    deltas = [0.0, 0.0]
    for step, mean, delta in zip(
        PATCH_STEPS, TARGET_MEAN_DENSITY, TARGET_GREEN_MINUS_RB
    ):
        if int(step) in TRAIN_STEPS:
            means.append(float(mean))
            deltas.append(float(delta))
    means.append(4.15)
    deltas.append(0.0)
    order = np.argsort(means)
    return np.asarray(means)[order], np.asarray(deltas)[order]


TRAIN_MEAN_DENSITY, TRAIN_GREEN_MINUS_RB = _training_curve()


def target_green_crossover(mean_density: np.ndarray) -> np.ndarray:
    return np.interp(
        mean_density,
        TRAIN_MEAN_DENSITY,
        TRAIN_GREEN_MINUS_RB,
        left=0.0,
        right=0.0,
    )


def apply_green_crossover(status_a: np.ndarray) -> np.ndarray:
    target = np.asarray(status_a, dtype=np.float64).copy()
    mean_density = np.mean(target, axis=-1)
    current_delta = target[..., 1] - 0.5 * (target[..., 0] + target[..., 2])
    correction = target_green_crossover(mean_density) - current_delta
    target[..., 0] -= correction / 3.0
    target[..., 1] += 2.0 * correction / 3.0
    target[..., 2] -= correction / 3.0
    return np.clip(target, 0.0, emulsion.PRINT_2383_DMAX).astype(np.float32)


def build_dle_shapers() -> tuple[list[np.ndarray], list[np.ndarray]]:
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
    target = apply_green_crossover(proportional)

    x_tables: list[np.ndarray] = []
    y_tables: list[np.ndarray] = []
    for channel in range(3):
        order = np.argsort(raw[:, channel])
        x = raw[order, channel]
        y = target[order, channel]
        x, unique_indices = np.unique(x, return_index=True)
        y = y[unique_indices]
        x_tables.append(x.astype(np.float32))
        y_tables.append(y.astype(np.float32))
    return x_tables, y_tables


def dle_print_density(negative_density_rgb: np.ndarray) -> np.ndarray:
    global _DLE_SHAPERS
    if _DLE_SHAPERS is None:
        _DLE_SHAPERS = build_dle_shapers()
    raw = emulsion._raw_print_2383_density_from_negative(negative_density_rgb)
    x_tables, y_tables = _DLE_SHAPERS
    calibrated = np.empty_like(raw)
    for channel in range(3):
        calibrated[..., channel] = np.interp(
            raw[..., channel], x_tables[channel], y_tables[channel]
        ).astype(np.float32)
    return calibrated


def build_dle_view_table() -> tuple[np.ndarray, np.ndarray]:
    mean_density = np.linspace(0.0, emulsion.PRINT_2383_DMAX, 513)
    proportional = mean_density[:, None] * KODAK_AIM[None, :] / LAD_MEAN
    status_a = apply_green_crossover(proportional)
    callier = emulsion.apply_2383_callier_density(status_a[None, ...])
    rgb = np.maximum(emulsion.apply_2383_projection_lut(callier)[0], 1e-8)
    luma = np.einsum("...c,c->...", rgb, LUMA_WEIGHTS)
    factors = luma[:, None] / rgb
    order = np.argsort(luma)
    return (
        luma[order].astype(np.float32),
        np.clip(factors[order], 0.35, 2.50).astype(np.float32),
    )


def dle_view_neutralizer(projected: np.ndarray) -> np.ndarray:
    global _DLE_VIEW_TABLE
    if _DLE_VIEW_TABLE is None:
        _DLE_VIEW_TABLE = build_dle_view_table()
    luma_axis, factor_table = _DLE_VIEW_TABLE
    source = np.maximum(np.asarray(projected, dtype=np.float32), 0.0)
    luma = np.einsum("...c,c->...", source, LUMA_WEIGHTS)
    corrected = np.empty_like(source)
    for channel in range(3):
        factor = np.interp(luma, luma_axis, factor_table[:, channel])
        corrected[..., channel] = source[..., channel] * factor
    return np.maximum(corrected, 0.0).astype(np.float32)


def set_mode(mode: str) -> None:
    if mode in ("v21_equal", "kodak_ad_lad_view"):
        previous.set_mode(mode)
        return
    if mode == "kodak_unshaped":
        emulsion._raw_print_2383_density_from_negative = (
            lambda negative_density_rgb: status_run.raw_print_with_aim(
                negative_density_rgb, status_run.KODAK_AIM
            )
        )
        emulsion.print_2383_density_from_negative = status_run.unshaped_print_density
        emulsion.neutralize_2383_projected_gray_scale = previous.lad_trajectory_view_neutralizer
        reset_caches()
        return
    if mode == "patent_dle_holdout":
        emulsion._raw_print_2383_density_from_negative = (
            lambda negative_density_rgb: status_run.raw_print_with_aim(
                negative_density_rgb, status_run.KODAK_AIM
            )
        )
        emulsion.print_2383_density_from_negative = dle_print_density
        emulsion.neutralize_2383_projected_gray_scale = dle_view_neutralizer
        reset_caches()
        return
    raise KeyError(mode)


MODES = ("v21_equal", "kodak_ad_lad_view", "kodak_unshaped", "patent_dle_holdout")


def neutral_trajectory(mode: str) -> tuple[np.ndarray, np.ndarray]:
    set_mode(mode)
    stops = np.linspace(-12.0, 9.0, 337, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    negative = emulsion.negative_total_printer_density(neutral)
    shaped = emulsion.print_2383_density_from_negative(negative).astype(np.float64)
    mean_density = np.mean(shaped, axis=1)
    green_delta = shaped[:, 1] - 0.5 * (shaped[:, 0] + shaped[:, 2])
    order = np.argsort(mean_density)
    return mean_density[order], green_delta[order]


def trajectory_gate(mode: str) -> dict[str, object]:
    mean_axis, delta_axis = neutral_trajectory(mode)
    predicted = np.interp(TARGET_MEAN_DENSITY, mean_axis, delta_axis)
    errors = predicted - TARGET_GREEN_MINUS_RB
    train_mask = np.array([int(step) in TRAIN_STEPS for step in PATCH_STEPS])
    holdout_mask = np.array([int(step) in HOLDOUT_STEPS for step in PATCH_STEPS])
    return {
        "predicted_green_minus_rb_density": predicted.astype(float).tolist(),
        "error_density": errors.astype(float).tolist(),
        "all_point_rmse_density": float(np.sqrt(np.mean(np.square(errors)))),
        "training_rmse_density": float(np.sqrt(np.mean(np.square(errors[train_mask])))),
        "holdout_rmse_density": float(np.sqrt(np.mean(np.square(errors[holdout_mask])))),
        "holdout_max_abs_error_density": float(np.max(np.abs(errors[holdout_mask]))),
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
        "probe_note": "Representative scene-neutral stops; separate from patent patch numbers.",
        "probe_stops_from_18_percent": probe_stops.astype(float).tolist(),
        "status_a": status_a.astype(float).tolist(),
        "corrected_oklab_chroma": chroma.astype(float).tolist(),
        "corrected_oklab_chroma_mean": float(np.mean(chroma)),
        "corrected_oklab_chroma_max": float(np.max(chroma)),
    }


def patch_gate(mode: str) -> dict[str, object]:
    set_mode(mode)
    return previous._patch_gate_current()


def save_digitization() -> None:
    with (OUTPUT / "digitized_dle_green_crossover.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "patch_step",
                "role",
                "red_blue_midpoint_x_px",
                "green_x_px",
                "red_blue_midpoint_status_a_density",
                "green_status_a_density",
                "mean_status_a_density",
                "green_minus_red_blue_midpoint_density",
                "single_curve_reading_uncertainty_density",
            ]
        )
        for step, rb_x, green_x, rb_d, green_d, mean_d, delta in zip(
            PATCH_STEPS,
            RB_MIDPOINT_X,
            GREEN_X,
            RB_DENSITY,
            GREEN_DENSITY,
            TARGET_MEAN_DENSITY,
            TARGET_GREEN_MINUS_RB,
        ):
            writer.writerow(
                [
                    int(step),
                    "training" if int(step) in TRAIN_STEPS else "holdout",
                    rb_x,
                    green_x,
                    rb_d,
                    green_d,
                    mean_d,
                    delta,
                    DENSITY_UNCERTAINTY,
                ]
            )


def save_validation_plot(gates: dict[str, dict[str, object]]) -> None:
    canvas = np.full((900, 1500, 3), 248, dtype=np.uint8)
    left, right, top, bottom = 130, 1430, 90, 790
    cv2.rectangle(canvas, (left, top), (right, bottom), (35, 35, 35), 2)
    x_min, x_max = 1.0, 4.2
    y_min, y_max = -0.34, 0.18

    def xy(mean: float, delta: float) -> tuple[int, int]:
        x = left + int((mean - x_min) / (x_max - x_min) * (right - left))
        y = bottom - int((delta - y_min) / (y_max - y_min) * (bottom - top))
        return x, y

    zero_y = xy(x_min, 0.0)[1]
    cv2.line(canvas, (left, zero_y), (right, zero_y), (170, 170, 170), 1)
    colors = {
        "v21_equal": (80, 80, 80),
        "kodak_ad_lad_view": (180, 100, 40),
        "kodak_unshaped": (60, 130, 190),
        "patent_dle_holdout": (40, 140, 60),
    }
    for mode, gate in gates.items():
        predicted = np.asarray(gate["predicted_green_minus_rb_density"], dtype=float)
        points = [xy(float(m), float(d)) for m, d in zip(TARGET_MEAN_DENSITY, predicted)]
        cv2.polylines(canvas, [np.asarray(points, dtype=np.int32)], False, colors[mode], 3)
    for step, mean, delta in zip(PATCH_STEPS, TARGET_MEAN_DENSITY, TARGET_GREEN_MINUS_RB):
        point = xy(float(mean), float(delta))
        if int(step) in HOLDOUT_STEPS:
            cv2.drawMarker(canvas, point, (15, 15, 15), cv2.MARKER_TILTED_CROSS, 18, 3)
        else:
            cv2.circle(canvas, point, 7, (15, 15, 15), -1)
        cv2.putText(canvas, str(int(step)), (point[0] + 8, point[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 1, cv2.LINE_AA)
    cv2.putText(canvas, "US6987586B2 Fig. 3: 2383 neutral DLE green crossover", (130, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (25, 25, 25), 2, cv2.LINE_AA)
    cv2.putText(canvas, "x: mean Status-A density", (560, 855), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 40, 40), 2, cv2.LINE_AA)
    cv2.putText(canvas, "filled = fit, x = blind holdout", (950, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 1, cv2.LINE_AA)
    cv2.imwrite(str(OUTPUT / "dle_holdout_validation.png"), canvas)


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
    ensure_source_figure()
    save_digitization()

    trajectory_gates = {mode: trajectory_gate(mode) for mode in MODES}
    save_validation_plot(trajectory_gates)

    raw = status_run.decode_frame()
    set_mode("v21_equal")
    baseline_projection = previous.render(raw, "v21_equal", "2383_projection_monitor")
    set_mode("kodak_ad_lad_view")
    proportional_projection = previous.render(
        raw, "kodak_ad_lad_view", "2383_projection_monitor"
    )
    set_mode("patent_dle_holdout")
    candidate_projection = emulsion.reconstruct_through_emulsion(
        raw,
        status_run.FRAME_INDEX,
        grain_scale=1.0,
        oversample=1,
        exposure_stops=status_run.EXPOSURE_STOPS,
        look="2383_projection_monitor",
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )
    set_mode("v21_equal")
    baseline_scan = previous.render(raw, "v21_equal", "cineon_bluray")
    set_mode("patent_dle_holdout")
    candidate_scan = emulsion.reconstruct_through_emulsion(
        raw,
        status_run.FRAME_INDEX,
        grain_scale=1.0,
        oversample=1,
        exposure_stops=status_run.EXPOSURE_STOPS,
        look="cineon_bluray",
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )

    status_run.save_rgb(
        OUTPUT / "baseline_v21_equal.png", status_run.to_srgb_u8(baseline_projection)
    )
    result = {
        "question": "Does the independent 2383 control-neutral DLE series support an equal/proportional Status-A neutral trajectory, or a density-dependent green crossover?",
        "source_figure": {
            "url": FIGURE_URL,
            "sha256": FIGURE_SHA256,
            "patent": "US6987586B2 Figure 3",
            "description": "Kodak VISION 2383 control neutral exposure DLE series, Status-A RGB, 21 patch steps",
        },
        "input": str(status_run.INPUT),
        "decode": "12-bit ProRes RAW via AVFoundation extended-linear BT.2020 float32",
        "frame": status_run.FRAME_INDEX,
        "dimensions": [status_run.TEST_WIDTH, status_run.TEST_HEIGHT],
        "exposure_stops": status_run.EXPOSURE_STOPS,
        "seed_policy": "V21 deterministic frame-index seed; identical for every variant",
        "digitization": {
            "patch_steps": PATCH_STEPS.astype(int).tolist(),
            "training_steps": sorted(TRAIN_STEPS),
            "blind_holdout_steps": sorted(HOLDOUT_STEPS),
            "red_blue_midpoint_x_px": RB_MIDPOINT_X.astype(float).tolist(),
            "green_x_px": GREEN_X.astype(float).tolist(),
            "target_mean_status_a_density": TARGET_MEAN_DENSITY.astype(float).tolist(),
            "target_green_minus_red_blue_midpoint_density": TARGET_GREEN_MINUS_RB.astype(float).tolist(),
            "single_curve_reading_uncertainty_density": DENSITY_UNCERTAINTY,
            "boundary": "Red and blue are not independently claimed where their solid/dotted strokes overlap; only the green-minus-red/blue-midpoint crossover is tested.",
        },
        "controlled_variables": "Only the 2383 neutral Status-A shaper and its corresponding post-spectral neutral table change. RAW decode, +0.45 stop, 5279 H-D/chemistry/DIR/morphology/seed, 3200 K printer model, 2383 base curves/dyes, Callier term, xenon SPD, H-61 colour guard, monitor adaptation and scan branch remain fixed.",
        "trajectory_gate": trajectory_gates,
        "view_gate": {
            mode: view_gate(mode)
            for mode in ("v21_equal", "kodak_ad_lad_view", "patent_dle_holdout")
        },
        "patch_gate": {
            mode: patch_gate(mode)
            for mode in ("v21_equal", "kodak_ad_lad_view", "patent_dle_holdout")
        },
        "frame_ab_vs_v21": previous.previous.compare(
            "patent_dle_holdout", baseline_projection, candidate_projection
        ),
        "frame_ab_vs_proportional": previous.previous.compare(
            "patent_dle_vs_proportional", proportional_projection, candidate_projection
        ),
        "scan_branch_isolation": previous.previous.compare(
            "scan_isolation", baseline_scan, candidate_scan
        ),
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
