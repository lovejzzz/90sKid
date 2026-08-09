"""Research-only 2383 hard-dye cross-talk neutral-trajectory test.

The archived 2005 sheet supplies three separated-light Status-A characteristic
curves, while US 6,987,586 supplies the 2383 Status-A-to-analytical-dye matrix
and a simultaneous control-neutral DLE holdout.  This script asks whether the
matrix can turn the separated curves into the simultaneous neutral trajectory.
Production code and formal V21 outputs are never modified.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT = ROOT / "experiments" / "emulsion_reconstruction"
PREVIOUS_DIR = EXPERIMENT / "research_runs" / "2026-08-03_2383_rgb_dle_trace"
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(EXPERIMENT / "src"))
import emulsion_experiment as emulsion


spec = importlib.util.spec_from_file_location("rgb_dle_trace", PREVIOUS_DIR / "run_ab.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import preceding RGB DLE run")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
previous.OUTPUT = OUTPUT
previous.previous.OUTPUT = OUTPUT
previous.status_run.OUTPUT = OUTPUT

ARCHIVED_CURVES = PREVIOUS_DIR / "archived_2005_2383_curves.csv"
PREVIOUS_METRICS = PREVIOUS_DIR / "metrics.json"
INPUT = previous.status_run.INPUT
FRAME_INDEX = 144
TRAIN_INDICES = np.array([0, 2, 4, 6])
HOLDOUT_INDICES = np.array([1, 3, 5])
LAD_STATUS_A = np.array([1.09, 1.06, 1.03], dtype=np.float64)
STATUS_A_TO_ANALYTICAL_DYE = np.array(
    [
        [0.3260, -0.0402, -0.0287],
        [-0.3380, 0.3859, 0.3166],
        [-0.0017, -0.0361, 0.3677],
    ],
    dtype=np.float64,
)
ANALYTICAL_DYE_TO_STATUS_A = np.linalg.inv(STATUS_A_TO_ANALYTICAL_DYE)
LAD_ANALYTICAL_DYE = STATUS_A_TO_ANALYTICAL_DYE @ LAD_STATUS_A
PATENT_STATUS_A = previous.TARGET_STATUS_A.astype(np.float64)
PATENT_MEAN = np.mean(PATENT_STATUS_A, axis=1)
PATENT_DEPARTURE = PATENT_STATUS_A - PATENT_MEAN[:, None]

ORIGINAL_RAW_PRINT = emulsion._raw_print_2383_density_from_negative
ORIGINAL_PRINT = emulsion.print_2383_density_from_negative
ORIGINAL_VIEW = emulsion.neutralize_2383_projected_gray_scale
_SHAPERS: tuple[list[np.ndarray], list[np.ndarray]] | None = None
_VIEW_TABLE: tuple[np.ndarray, np.ndarray] | None = None


def load_archived_curves() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    with ARCHIVED_CURVES.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {}
    for channel in "RGB":
        values = np.array(
            [
                (float(row["log_exposure_lux_seconds"]), float(row["status_a_density"]))
                for row in rows
                if row["channel"] == channel
            ],
            dtype=np.float64,
        )
        result[channel] = (values[:, 0], values[:, 1])
    return result


CURVES = load_archived_curves()


def build_hard_dye_trajectory() -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    """Combine separated curves as dye amounts, then apply the published matrix."""
    lad_log_exposure = []
    dmin = []
    for index, channel in enumerate("RGB"):
        log_exposure, density = CURVES[channel]
        order = np.argsort(density)
        lad_log_exposure.append(
            float(np.interp(LAD_STATUS_A[index], density[order], log_exposure[order]))
        )
        dmin.append(float(np.min(density)))

    relative_exposure = np.linspace(-2.0, 2.0, 8001, dtype=np.float64)
    separated_principal_density = np.stack(
        [
            np.interp(relative_exposure + lad_log_exposure[index], *CURVES[channel])
            for index, channel in enumerate("RGB")
        ],
        axis=1,
    )
    dmin_array = np.asarray(dmin, dtype=np.float64)

    # Each separated-light curve provides only its principal Status-A density.
    # Convert that principal response into a LAD-normalized dye amount.  The
    # published inverse hard-dye matrix then supplies all cross-densities.
    normalized_principal = (separated_principal_density - dmin_array) / (
        LAD_STATUS_A - dmin_array
    )
    analytical_dye = normalized_principal * LAD_ANALYTICAL_DYE
    # Accelerated float libraries on this host can emit false status warnings
    # for finite matrix products; validate the result explicitly below.
    with np.errstate(all="ignore"):
        predicted_status_a = analytical_dye @ ANALYTICAL_DYE_TO_STATUS_A.T
    if not np.all(np.isfinite(predicted_status_a)):
        raise RuntimeError("non-finite hard-dye trajectory")
    predicted_mean = np.mean(predicted_status_a, axis=1)
    order = np.argsort(predicted_mean)
    predicted_mean = predicted_mean[order]
    predicted_status_a = predicted_status_a[order]

    at_patent = np.stack(
        [
            np.interp(PATENT_MEAN, predicted_mean, predicted_status_a[:, channel])
            for channel in range(3)
        ],
        axis=1,
    )
    at_patent_departure = at_patent - np.mean(at_patent, axis=1, keepdims=True)

    # One bounded calibration freedom: the strength of the matrix-predicted
    # chromatic departure.  Fit only even patent steps and keep mean tone fixed.
    numerator = float(np.sum(at_patent_departure[TRAIN_INDICES] * PATENT_DEPARTURE[TRAIN_INDICES]))
    denominator = float(np.sum(np.square(at_patent_departure[TRAIN_INDICES])))
    strength = float(np.clip(numerator / denominator, 0.0, 1.0))
    calibrated_at_patent = PATENT_MEAN[:, None] + strength * at_patent_departure

    trajectory_departure = predicted_status_a - predicted_mean[:, None]
    calibrated_status_a = predicted_mean[:, None] + strength * trajectory_departure
    details = {
        "lad_log_exposure": lad_log_exposure,
        "separated_curve_dmin": dmin,
        "published_matrix": STATUS_A_TO_ANALYTICAL_DYE.astype(float).tolist(),
        "inverse_hard_dye_matrix": ANALYTICAL_DYE_TO_STATUS_A.astype(float).tolist(),
        "lad_analytical_dye": LAD_ANALYTICAL_DYE.astype(float).tolist(),
        "parameter_free_status_a_at_patent_means": at_patent.astype(float).tolist(),
        "calibrated_cross_talk_strength": strength,
        "calibrated_status_a_at_patent_means": calibrated_at_patent.astype(float).tolist(),
    }
    return predicted_mean, calibrated_status_a, details


MODEL_MEAN, MODEL_STATUS_A, MODEL_DETAILS = build_hard_dye_trajectory()


def model_status_at_mean(mean_density: np.ndarray) -> np.ndarray:
    mean = np.asarray(mean_density, dtype=np.float64)
    return np.stack(
        [np.interp(mean, MODEL_MEAN, MODEL_STATUS_A[:, channel]) for channel in range(3)],
        axis=-1,
    )


def reset_caches() -> None:
    global _SHAPERS, _VIEW_TABLE
    _SHAPERS = None
    _VIEW_TABLE = None
    previous.reset_caches()


def build_shapers() -> tuple[list[np.ndarray], list[np.ndarray]]:
    stops = np.linspace(-12.0, 9.0, 337, dtype=np.float32)
    levels = 0.18 * np.power(2.0, stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    raw = emulsion._raw_print_2383_density_from_negative(
        emulsion.negative_total_printer_density(neutral)
    ).astype(np.float64)
    target = model_status_at_mean(np.mean(raw, axis=1))
    x_tables: list[np.ndarray] = []
    y_tables: list[np.ndarray] = []
    for channel in range(3):
        order = np.argsort(raw[:, channel])
        x, unique = np.unique(raw[order, channel], return_index=True)
        x_tables.append(x.astype(np.float32))
        y_tables.append(target[order, channel][unique].astype(np.float32))
    return x_tables, y_tables


def model_print_density(negative_density_rgb: np.ndarray) -> np.ndarray:
    global _SHAPERS
    if _SHAPERS is None:
        _SHAPERS = build_shapers()
    raw = emulsion._raw_print_2383_density_from_negative(negative_density_rgb)
    calibrated = np.empty_like(raw)
    for channel in range(3):
        calibrated[..., channel] = np.interp(
            raw[..., channel], _SHAPERS[0][channel], _SHAPERS[1][channel]
        ).astype(np.float32)
    return calibrated


def build_view_table() -> tuple[np.ndarray, np.ndarray]:
    mean_density = np.linspace(0.0, emulsion.PRINT_2383_DMAX, 513)
    status_a = model_status_at_mean(mean_density).astype(np.float32)
    callier = emulsion.apply_2383_callier_density(status_a[None, ...])
    rgb = np.maximum(emulsion.apply_2383_projection_lut(callier)[0], 1e-8)
    luma = np.einsum("...c,c->...", rgb, previous.LUMA_WEIGHTS)
    factors = luma[:, None] / rgb
    order = np.argsort(luma)
    return luma[order].astype(np.float32), np.clip(factors[order], 0.35, 2.50).astype(np.float32)


def model_view_neutralizer(projected: np.ndarray) -> np.ndarray:
    global _VIEW_TABLE
    if _VIEW_TABLE is None:
        _VIEW_TABLE = build_view_table()
    source = np.maximum(np.asarray(projected, dtype=np.float32), 0.0)
    luma = np.einsum("...c,c->...", source, previous.LUMA_WEIGHTS)
    corrected = np.empty_like(source)
    for channel in range(3):
        factor = np.interp(luma, _VIEW_TABLE[0], _VIEW_TABLE[1][:, channel])
        corrected[..., channel] = source[..., channel] * factor
    return np.maximum(corrected, 0.0).astype(np.float32)


def set_candidate() -> None:
    emulsion._raw_print_2383_density_from_negative = (
        lambda negative_density_rgb: previous.status_run.raw_print_with_aim(
            negative_density_rgb, previous.status_run.KODAK_AIM
        )
    )
    emulsion.print_2383_density_from_negative = model_print_density
    emulsion.neutralize_2383_projected_gray_scale = model_view_neutralizer
    reset_caches()


def render_candidate(raw: np.ndarray, look: str) -> np.ndarray:
    set_candidate()
    return emulsion.reconstruct_through_emulsion(
        raw,
        FRAME_INDEX,
        grain_scale=1.0,
        oversample=1,
        exposure_stops=previous.status_run.EXPOSURE_STOPS,
        look=look,
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )


def density_metrics(predicted: np.ndarray) -> dict[str, object]:
    error = predicted - PATENT_STATUS_A
    return {
        "predicted_status_a_rgb": predicted.astype(float).tolist(),
        "error_status_a_rgb": error.astype(float).tolist(),
        "all_point_rmse_density": float(np.sqrt(np.mean(np.square(error)))),
        "training_rmse_density": float(np.sqrt(np.mean(np.square(error[TRAIN_INDICES])))),
        "blind_holdout_rmse_density": float(np.sqrt(np.mean(np.square(error[HOLDOUT_INDICES])))),
        "blind_holdout_max_abs_error_density": float(np.max(np.abs(error[HOLDOUT_INDICES]))),
        "predicted_red_minus_blue_density": (predicted[:, 0] - predicted[:, 2]).astype(float).tolist(),
        "target_red_minus_blue_density": (PATENT_STATUS_A[:, 0] - PATENT_STATUS_A[:, 2]).astype(float).tolist(),
    }


def save_plot(parameter_free: np.ndarray, calibrated: np.ndarray) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), constrained_layout=True)
    steps = previous.PATCH_STEPS
    colors = ("#c83f31", "#3c8b5f", "#355c9b")
    for index, (label, color) in enumerate(zip("RGB", colors)):
        axes[0].plot(steps, PATENT_STATUS_A[:, index], "o-", color=color, label=f"Patent {label}")
        axes[0].plot(steps, calibrated[:, index], "--", color=color, alpha=0.72, label=f"Model {label}")
    axes[0].set(title="2383 simultaneous-neutral Status-A", xlabel="Patent patch step", ylabel="Density D")
    axes[0].invert_xaxis()
    axes[0].legend(ncol=2, fontsize=8)
    axes[0].grid(alpha=0.2)
    axes[1].axhline(0.0, color="#777", linewidth=1)
    axes[1].plot(steps, PATENT_STATUS_A[:, 0] - PATENT_STATUS_A[:, 2], "o-", color="#111", label="Patent R-B")
    axes[1].plot(steps, parameter_free[:, 0] - parameter_free[:, 2], "--", color="#c07a1a", label="Hard-dye R-B")
    axes[1].plot(steps, calibrated[:, 0] - calibrated[:, 2], ":", color="#7b3fa1", linewidth=2, label="Even-fit R-B")
    axes[1].set(title="R/B sign reversal test", xlabel="Patent patch step", ylabel="R - B density D")
    axes[1].invert_xaxis()
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.2)
    fig.savefig(OUTPUT / "hard_dye_holdout.png", dpi=180)
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    parameter_free = np.asarray(MODEL_DETAILS["parameter_free_status_a_at_patent_means"])
    calibrated = np.asarray(MODEL_DETAILS["calibrated_status_a_at_patent_means"])
    save_plot(parameter_free, calibrated)

    with PREVIOUS_METRICS.open(encoding="utf-8") as handle:
        prior_metrics = json.load(handle)
    prior_holdout = prior_metrics["trajectory_gate"]["patent_rgb_holdout"]["all_channel_blind_holdout_rmse_density"]

    raw = previous.decode_frame(FRAME_INDEX)
    baseline = previous.render(raw, FRAME_INDEX, "v21_equal", "2383_projection_monitor")
    candidate = render_candidate(raw, "2383_projection_monitor")
    frame_metrics = previous.compare("hard_dye_frame144", baseline, candidate)
    baseline_scan = previous.render(raw, FRAME_INDEX, "v21_equal", "cineon_bluray")
    candidate_scan = render_candidate(raw, "cineon_bluray")
    scan_metrics = previous.compare("hard_dye_scan_isolation_frame144", baseline_scan, candidate_scan)

    set_candidate()
    patch_metrics = previous.previous.previous._patch_gate_current()
    set_candidate()
    # Evaluate the candidate neutral view directly because the preceding helper
    # selects only its own named modes.
    probe_stops = np.array([-3, -2, -1, 0, 1, 2], dtype=np.float32)
    levels = 0.18 * np.power(2.0, probe_stops)
    neutral = np.repeat(levels[:, None], 3, axis=1).astype(np.float32)
    status_a = emulsion.print_2383_density_from_negative(emulsion.negative_total_printer_density(neutral))
    spectral = emulsion.apply_2383_projection_lut(emulsion.apply_2383_callier_density(status_a[None, ...]))[0]
    corrected = emulsion.neutralize_2383_projected_gray_scale(np.maximum(spectral, 0.0))
    lab = emulsion.linear_rec709_to_oklab(corrected[None, ...])[0]
    chroma = np.linalg.norm(lab[:, 1:3], axis=1)

    result = {
        "question": "Can Kodak's 2383 hard-dye matrix combine archived separated-light curves into the patent's simultaneous-neutral RGB DLE trajectory?",
        "sources": {
            "matrix_and_neutral_holdout": "US6987586B2 / US20020163657A1, Figure 3 and matrix example",
            "separated_curves": "Kodak H-1-2383t, revised March 2005, page 5 vector paths",
            "spectral_boundary": "The 2383 dye-density graph supplies dye absorption curves but not the Status-A densitometer spectral response functions; it cannot independently replace the published hard-dye matrix.",
        },
        "input": str(INPUT),
        "decode": "12-bit ProRes RAW via AVFoundation extended-linear BT.2020 float32",
        "frame": FRAME_INDEX,
        "dimensions": [previous.status_run.TEST_WIDTH, previous.status_run.TEST_HEIGHT],
        "seed_policy": "V21 deterministic frame-index seed; identical within A/B",
        "controlled_variables": "Only the 2383 neutral Status-A trajectory and its matching projected-neutral table change. RAW decode, +0.45 stop, 5279 development/DIR/dye clouds/grain, printer model, base 2383 curves/dyes, Callier term, xenon observer, H-61 guard, monitor adaptation and scan branch remain fixed.",
        "model": MODEL_DETAILS,
        "density_gate": {
            "parameter_free_hard_dye": density_metrics(parameter_free),
            "even_step_calibrated_strength": density_metrics(calibrated),
            "previous_best_blind_holdout_rmse_density": prior_holdout,
        },
        "raw_frame_ab_vs_v21": frame_metrics,
        "scan_branch_isolation": scan_metrics,
        "six_colour_candidate": patch_metrics,
        "neutral_view_candidate": {
            "probe_stops": probe_stops.astype(float).tolist(),
            "corrected_oklab_chroma": chroma.astype(float).tolist(),
            "mean": float(np.mean(chroma)),
            "max": float(np.max(chroma)),
        },
        "release_gate": {
            "beats_previous_density_holdout": bool(density_metrics(calibrated)["blind_holdout_rmse_density"] < prior_holdout),
            "decision": "reject",
        },
    }
    (OUTPUT / "metrics.json").write_text(
        json.dumps(previous.json_safe(result), ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    emulsion._raw_print_2383_density_from_negative = ORIGINAL_RAW_PRINT
    emulsion.print_2383_density_from_negative = ORIGINAL_PRINT
    emulsion.neutralize_2383_projected_gray_scale = ORIGINAL_VIEW
    reset_caches()


if __name__ == "__main__":
    main()
