"""Research-only ISO Status-A spectral-product holdout for Kodak 2383.

This test asks whether the exact published Status-A spectral weighting factors,
combined with the digitized 2383 CMY dye-density curves, can recover the
simultaneous-neutral DLE trajectory without an empirical cross-talk parameter.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import least_squares


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src" / "emulsion_experiment.py"
PREVIOUS_DIR = ROOT / "research_runs" / "2026-08-03_2383_hard_dye_cross_talk"
CURVE_CSV = ROOT / "research_runs" / "2026-08-03_2383_rgb_dle_trace" / "archived_2005_2383_curves.csv"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


emulsion = load_module("emulsion_status_a_holdout", SRC)
previous = load_module("previous_hard_dye_holdout", PREVIOUS_DIR / "run_ab.py")

LAD_STATUS_A = previous.LAD_STATUS_A.astype(np.float64)
PATENT_STATUS_A = previous.PATENT_STATUS_A.astype(np.float64)
PATENT_MEAN = np.mean(PATENT_STATUS_A, axis=1)
TRAIN_INDICES = previous.TRAIN_INDICES
HOLDOUT_INDICES = previous.HOLDOUT_INDICES

# ISO 5-3:2009 Table 9, 10 nm abridged Status-A standard-density weighting
# factors. Columns are blue, green and red. The full tabulated range sums to
# 100 in each channel. Small negative entries are interpolation weights, not
# negative physical spectral products.
WAVELENGTH_NM = np.arange(340.0, 771.0, 10.0, dtype=np.float64)
STATUS_A_BGR_WEIGHTS = np.array(
    [
        [0.000, 0.000, 0.000], [0.000, 0.000, 0.000],
        [0.000, 0.000, 0.000], [0.000, 0.000, 0.000],
        [0.000, 0.000, 0.000], [0.000, 0.000, 0.000],
        [-0.003, 0.000, 0.000], [-0.373, 0.000, 0.000],
        [2.763, 0.000, 0.000], [20.848, 0.000, 0.000],
        [32.395, 0.000, 0.000], [26.684, 0.000, 0.000],
        [13.711, 0.000, 0.000], [3.723, 0.000, 0.000],
        [0.275, 0.000, 0.000], [-0.022, -0.012, 0.000],
        [-0.002, -0.256, 0.000], [0.000, 2.887, 0.000],
        [0.000, 19.135, 0.000], [0.000, 31.434, 0.000],
        [0.000, 25.840, 0.000], [0.000, 14.144, 0.000],
        [0.000, 5.365, 0.000], [0.000, 1.296, 0.000],
        [0.000, 0.166, -0.000], [0.000, 0.004, -0.108],
        [0.000, -0.002, -0.300], [0.000, 0.000, 16.166],
        [0.000, 0.000, 33.797], [0.000, 0.000, 25.312],
        [0.000, 0.000, 13.862], [0.000, 0.000, 6.532],
        [0.000, 0.000, 2.723], [0.000, 0.000, 1.185],
        [0.000, 0.000, 0.498], [0.000, 0.000, 0.201],
        [0.000, 0.000, 0.081], [0.000, 0.000, 0.031],
        [0.000, 0.000, 0.012], [0.000, 0.000, 0.005],
        [0.000, 0.000, 0.002], [0.000, 0.000, 0.001],
        [0.000, 0.000, 0.000], [0.000, 0.000, 0.000],
    ],
    dtype=np.float64,
)

# Convert the standard's B/G/R measurement order to R/G/B Status-A order.
STATUS_A_RGB_WEIGHTS = STATUS_A_BGR_WEIGHTS[:, [2, 1, 0]]


def load_archived_curves() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    with CURVE_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for channel in "RGB":
        values = np.array(
            [
                (float(row["log_exposure_lux_seconds"]), float(row["status_a_density"]))
                for row in rows
                if row["channel"] == channel
            ],
            dtype=np.float64,
        )
        order = np.argsort(values[:, 0])
        result[channel] = (values[order, 0], values[order, 1])
    return result


CURVES = load_archived_curves()
DMIN_RGB = np.array([np.min(CURVES[c][1]) for c in "RGB"], dtype=np.float64)

# Interpolate the 20 nm Kodak dye graph onto the ISO 10 nm grid. Extrapolated
# tails cannot affect the result materially because the corresponding Status-A
# weights are zero or extremely small.
DYE_CMY = np.stack(
    [
        np.interp(
            WAVELENGTH_NM,
            emulsion.PRINT_DYE_WAVELENGTHS_NM.astype(np.float64),
            emulsion.PRINT_DYE_CMY_SPECTRAL_DENSITY[:, channel].astype(np.float64),
        )
        for channel in range(3)
    ],
    axis=1,
)


def status_a_net_density(amount_cmy: np.ndarray, scale_cmy: np.ndarray) -> np.ndarray:
    """Integrate CMY spectral transmission through ISO Status-A weights."""
    amount = np.asarray(amount_cmy, dtype=np.float64)
    spectral_density = np.einsum("...c,wc,c->...w", amount, DYE_CMY, scale_cmy)
    transmission = np.power(10.0, -spectral_density)
    weighted = np.einsum("...w,wc->...c", transmission, STATUS_A_RGB_WEIGHTS)
    normalized = weighted / np.sum(STATUS_A_RGB_WEIGHTS, axis=0)
    return -np.log10(np.maximum(normalized, 1e-12))


# Keep the peak-normalized relative amplitudes of the Kodak dye graph. Absolute
# dye amounts are recovered below from each separated principal curve. The
# three exposure offsets are then solved only at the official LAD patch; this
# represents printer-light balance, not a fitted off-LAD colour trajectory.
DYE_SCALE = np.ones(3, dtype=np.float64)


def invert_principal_density(record: int, principal_net_density: np.ndarray) -> np.ndarray:
    amount_axis = np.linspace(0.0, 8.0, 16001, dtype=np.float64)
    samples = np.zeros((amount_axis.size, 3), dtype=np.float64)
    samples[:, record] = amount_axis
    principal_axis = status_a_net_density(samples, DYE_SCALE)[:, record]
    order = np.argsort(principal_axis)
    return np.interp(principal_net_density, principal_axis[order], amount_axis[order])


def amount_from_log_exposure(record: int, log_exposure: np.ndarray) -> np.ndarray:
    channel = "RGB"[record]
    curve_x, curve_y = CURVES[channel]
    principal = np.interp(log_exposure, curve_x, curve_y)
    return invert_principal_density(record, np.maximum(principal - DMIN_RGB[record], 0.0))


def solve_lad_exposure_offsets() -> tuple[np.ndarray, np.ndarray]:
    initial = np.array(
        [
            np.interp(LAD_STATUS_A[i], CURVES[c][1], CURVES[c][0])
            for i, c in enumerate("RGB")
        ],
        dtype=np.float64,
    )
    lower = np.array([CURVES[c][0].min() for c in "RGB"], dtype=np.float64)
    upper = np.array([CURVES[c][0].max() for c in "RGB"], dtype=np.float64)

    def residual(offsets: np.ndarray) -> np.ndarray:
        amount = np.array(
            [amount_from_log_exposure(i, offsets[i]) for i in range(3)],
            dtype=np.float64,
        )
        return status_a_net_density(amount, DYE_SCALE) + DMIN_RGB - LAD_STATUS_A

    result = least_squares(
        residual,
        initial,
        bounds=(lower, upper),
        xtol=1e-13,
        ftol=1e-13,
        gtol=1e-13,
    )
    if not result.success or np.max(np.abs(result.fun)) > 1e-7:
        raise RuntimeError(f"LAD printer-balance solve failed: {result.message}, residual={result.fun}")
    amounts = np.array(
        [amount_from_log_exposure(i, result.x[i]) for i in range(3)],
        dtype=np.float64,
    )
    return result.x, amounts


def build_spectral_trajectory() -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    lad_log_exposure, lad_amounts = solve_lad_exposure_offsets()
    relative_exposure = np.linspace(-2.0, 2.0, 8001, dtype=np.float64)
    amount = np.stack(
        [
            amount_from_log_exposure(i, relative_exposure + lad_log_exposure[i])
            for i in range(3)
        ],
        axis=1,
    )
    predicted = status_a_net_density(amount, DYE_SCALE) + DMIN_RGB
    mean_density = np.mean(predicted, axis=1)
    order = np.argsort(mean_density)
    mean_density = mean_density[order]
    predicted = predicted[order]
    at_patent = np.stack(
        [np.interp(PATENT_MEAN, mean_density, predicted[:, c]) for c in range(3)],
        axis=1,
    )

    eps = 1e-4
    base = status_a_net_density(lad_amounts, DYE_SCALE)
    jacobian = np.stack(
        [
            (status_a_net_density(lad_amounts + np.eye(3)[c] * eps, DYE_SCALE) - base) / eps
            for c in range(3)
        ],
        axis=1,
    )
    return mean_density, predicted, {
        "iso_weight_sums_rgb": np.sum(STATUS_A_RGB_WEIGHTS, axis=0).tolist(),
        "dmin_rgb": DMIN_RGB.tolist(),
        "dye_scale_cmy": DYE_SCALE.tolist(),
        "lad_log_exposure_offsets_rgb": lad_log_exposure.tolist(),
        "lad_dye_amounts_cmy": lad_amounts.tolist(),
        "lad_status_a_reconstructed": (status_a_net_density(lad_amounts, DYE_SCALE) + DMIN_RGB).tolist(),
        "status_a_per_dye_jacobian_at_lad": jacobian.tolist(),
        "inverse_jacobian_status_a_to_dye": np.linalg.inv(jacobian).tolist(),
        "predicted_at_patent_means": at_patent.tolist(),
    }


def density_metrics(predicted: np.ndarray) -> dict[str, object]:
    error = predicted - PATENT_STATUS_A

    def rmse(indices: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(error[indices]))))

    return {
        "all_rgb_rmse_density": float(np.sqrt(np.mean(np.square(error)))),
        "train_even_rgb_rmse_density": rmse(TRAIN_INDICES),
        "holdout_odd_rgb_rmse_density": rmse(HOLDOUT_INDICES),
        "holdout_max_abs_density_error": float(np.max(np.abs(error[HOLDOUT_INDICES]))),
        "target_red_minus_blue": (PATENT_STATUS_A[:, 0] - PATENT_STATUS_A[:, 2]).tolist(),
        "predicted_red_minus_blue": (predicted[:, 0] - predicted[:, 2]).tolist(),
        "error_rgb": error.tolist(),
    }


def main() -> None:
    _, _, details = build_spectral_trajectory()
    predicted = np.asarray(details["predicted_at_patent_means"], dtype=np.float64)
    metrics = {
        "question": "Can ISO Status-A weighting plus 2383 dye spectra explain the simultaneous-neutral DLE without empirical cross-talk?",
        "source_boundary": {
            "status_a": "ISO 5-3:2009 Table 9, 10 nm abridged weighting factors; sums normalized to 100.",
            "dye_spectra": "Kodak H-1-2383 graph, visually digitized at 20 nm; representative, peak-normalized data.",
            "separated_curves": "Archived Kodak H-1-2383t 2005 vector principal Status-A curves.",
            "target": "US 6,987,586 Figure 3 simultaneous-neutral 2383 DLE digitization, odd steps held blind.",
        },
        "model": details,
        "density_metrics": density_metrics(predicted),
        "decision_threshold": {
            "must_beat_prior_holdout_rmse_density": 0.02287,
            "must_predict_red_blue_sign_at_step_7": True,
        },
    }
    (HERE / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    steps = np.arange(2, 9)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for channel, color, label in zip(range(3), ("#c43d3d", "#27945c", "#365db8"), "RGB"):
        axes[0].plot(steps, PATENT_STATUS_A[:, channel], "o-", color=color, label=f"Patent {label}")
        axes[0].plot(steps, predicted[:, channel], "x--", color=color, alpha=0.75, label=f"ISO spectral {label}")
    axes[0].set(xlabel="Patent patch step", ylabel="Status-A density D", title="2383 simultaneous-neutral trajectory")
    axes[0].legend(ncol=2, fontsize=8)
    axes[0].grid(alpha=0.2)
    axes[1].plot(steps, PATENT_STATUS_A[:, 0] - PATENT_STATUS_A[:, 2], "o-", color="#111", label="Patent R-B")
    axes[1].plot(steps, predicted[:, 0] - predicted[:, 2], "x--", color="#8b4ab2", label="ISO spectral R-B")
    axes[1].axhline(0.0, color="#777", linewidth=0.8)
    axes[1].set(xlabel="Patent patch step", ylabel="R-B density D", title="Red/blue crossover sign")
    axes[1].legend()
    axes[1].grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(HERE / "status_a_spectral_holdout.png", dpi=180)
    print(json.dumps(metrics["density_metrics"], indent=2))


if __name__ == "__main__":
    main()
