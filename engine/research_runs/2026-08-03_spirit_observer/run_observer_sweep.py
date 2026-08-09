"""Bounded sensitivity study for V21's provisional Spirit/telecine observer.

This is a research diagnostic, not a production renderer.  DFT documents the
Spirit 2K optical path and stock-specific RGB correction but does not publish
its detector spectral response.  We therefore perturb the visually estimated
Kodak-patent peaks and widths, fit the documented 3x3 masking operation on a
synthetic calibration wedge, and test whether one family is uniquely better.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from itertools import product
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

BASE_CENTRES = np.array([620.0, 540.0, 470.0], dtype=np.float32)
BASE_SIGMAS = np.array([52.0, 44.0, 38.0], dtype=np.float32)


def weights_for(centres: np.ndarray, sigmas: np.ndarray) -> np.ndarray:
    wavelength = emulsion.NEGATIVE_DYE_WAVELENGTHS_NM[:, None]
    weights = np.exp(-0.5 * np.square((wavelength - centres[None, :]) / sigmas[None, :]))
    return (weights / np.sum(weights, axis=0, keepdims=True)).astype(np.float32)


def optical_density(records: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Integrate net 5279 dye spectra through one diagnostic observer."""
    axis, spectra, coefficient_axes = emulsion._negative_5279_spectral_amount_axes(257)
    coefficients = np.stack(
        [np.interp(records[:, c], axis, coefficient_axes[c]) for c in range(3)],
        axis=-1,
    )
    spectral_density = np.clip(coefficients @ spectra.T, -2.0, 16.0)
    transmission = np.power(10.0, -spectral_density)
    return -np.log10(np.maximum(transmission @ weights, 1e-8))


def calibration_sets() -> tuple[np.ndarray, np.ndarray]:
    """Six colour directions plus neutral, with disjoint train/holdout levels."""
    directions = np.array(
        [
            [1, 0, 0], [0, 1, 0], [0, 0, 1],
            [1, 1, 0], [1, 0, 1], [0, 1, 1],
            [1, 1, 1],
        ],
        dtype=np.float32,
    )
    train_levels = np.array([0.12, 0.35, 0.70, 1.10, 1.55], dtype=np.float32)
    holdout_levels = np.array([0.22, 0.52, 0.88, 1.32, 1.78], dtype=np.float32)
    train = np.concatenate([directions * level for level in train_levels], axis=0)
    holdout = np.concatenate([directions * level for level in holdout_levels], axis=0)
    return train, holdout


def evaluate_family(centres: np.ndarray, sigmas: np.ndarray) -> dict[str, object]:
    train, holdout = calibration_sets()
    weights = weights_for(centres, sigmas)
    train_raw = optical_density(train, weights)
    holdout_raw = optical_density(holdout, weights)
    matrix, _, _, _ = np.linalg.lstsq(train_raw, train, rcond=None)
    predicted = holdout_raw @ matrix
    error = predicted - holdout
    neutral = np.array([[v, v, v] for v in np.linspace(0.05, 1.9, 31)], dtype=np.float32)
    neutral_error = optical_density(neutral, weights) @ matrix - neutral
    singular = np.linalg.svd(matrix, compute_uv=False)
    return {
        "centres_nm": centres.astype(float).tolist(),
        "sigmas_nm": sigmas.astype(float).tolist(),
        "masking_matrix": matrix.astype(float).tolist(),
        "holdout_rms_density": float(np.sqrt(np.mean(np.square(error)))),
        "holdout_max_abs_density": float(np.max(np.abs(error))),
        "neutral_max_abs_density": float(np.max(np.abs(neutral_error))),
        "matrix_max_singular": float(np.max(singular)),
        "matrix_condition": float(np.max(singular) / np.min(singular)),
        "matrix_max_abs_coefficient": float(np.max(np.abs(matrix))),
    }


def reset_scanner_state(centres: np.ndarray, sigmas: np.ndarray) -> None:
    weights = weights_for(centres, sigmas)
    emulsion._negative_5279_period_telecine_weights = lambda: weights
    emulsion._NEGATIVE_5279_NET_DENSITY_LUT = None
    emulsion.NEUTRAL_MID_SCANNER_DENSITY = emulsion.scanner_density_from_total_record_density(
        emulsion.record_densities(
            emulsion.film_records_from_rgb(np.array([0.18, 0.18, 0.18], dtype=np.float32))
        )
    )
    emulsion.NEUTRAL_HIGH_SCANNER_DENSITY = emulsion.scanner_density_from_total_record_density(
        emulsion.record_densities(
            emulsion.film_records_from_rgb(np.array([10.0, 10.0, 10.0], dtype=np.float32))
        )
    )


def decode_frame() -> np.ndarray:
    expected = SOURCE_WIDTH * SOURCE_HEIGHT * 3 * 4
    result = subprocess.run(
        [str(DECODER), str(INPUT), str(FRAME_INDEX), "1"],
        check=True,
        stdout=subprocess.PIPE,
    )
    if len(result.stdout) != expected:
        raise RuntimeError(f"decoder returned {len(result.stdout)} bytes, expected {expected}")
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(SOURCE_HEIGHT, SOURCE_WIDTH, 3)
    return cv2.resize(raw, (TEST_WIDTH, TEST_HEIGHT), interpolation=cv2.INTER_AREA)


def render_scan(raw: np.ndarray, centres: np.ndarray, sigmas: np.ndarray) -> np.ndarray:
    reset_scanner_state(centres, sigmas)
    return emulsion.reconstruct_through_emulsion(
        raw,
        FRAME_INDEX,
        grain_scale=1.0,
        oversample=1,
        exposure_stops=EXPOSURE_STOPS,
        look="cineon_bluray",
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )


def to_srgb_u8(bt709: np.ndarray) -> np.ndarray:
    srgb = emulsion.srgb_encode(emulsion.bt709_decode(bt709))
    return np.rint(np.clip(srgb, 0.0, 1.0) * 255.0).astype(np.uint8)


def save_rgb(path: Path, image: np.ndarray) -> None:
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def frame_metrics(baseline: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    baseline_linear = emulsion.bt709_decode(baseline)
    candidate_linear = emulsion.bt709_decode(candidate)
    delta = candidate_linear - baseline_linear
    lab_a = emulsion.linear_rec709_to_oklab(np.clip(baseline_linear, 0.0, None))
    lab_b = emulsion.linear_rec709_to_oklab(np.clip(candidate_linear, 0.0, None))
    delta_e = np.linalg.norm(lab_b - lab_a, axis=-1)
    baseline_luma = np.einsum("...c,c->...", baseline_linear, [0.2126, 0.7152, 0.0722])
    candidate_luma = np.einsum("...c,c->...", candidate_linear, [0.2126, 0.7152, 0.0722])
    mse = float(np.mean(np.square(delta)))
    a8 = to_srgb_u8(baseline)
    b8 = to_srgb_u8(candidate)
    save_rgb(OUTPUT / "baseline_scan.png", a8)
    save_rgb(OUTPUT / "candidate_scan.png", b8)
    save_rgb(OUTPUT / "ab_scan.png", np.concatenate([a8, b8], axis=1))
    save_rgb(
        OUTPUT / "difference_x16_scan.png",
        np.rint(np.clip(0.5 + 16.0 * delta, 0.0, 1.0) * 255.0).astype(np.uint8),
    )
    return {
        "linear_rgb_mae": float(np.mean(np.abs(delta))),
        "linear_rgb_max_abs": float(np.max(np.abs(delta))),
        "psnr_db": float("inf") if mse == 0 else float(-10.0 * np.log10(mse)),
        "oklab_delta_e_median": float(np.median(delta_e)),
        "oklab_delta_e_p95": float(np.percentile(delta_e, 95)),
        "oklab_delta_e_p99": float(np.percentile(delta_e, 99)),
        "oklab_median_a_shift": float(np.median(lab_b[..., 1] - lab_a[..., 1])),
        "oklab_median_b_shift": float(np.median(lab_b[..., 2] - lab_a[..., 2])),
        "luma_delta_p95_abs": float(np.percentile(np.abs(candidate_luma - baseline_luma), 95)),
        "baseline_luma_p1": float(np.percentile(baseline_luma, 1)),
        "candidate_luma_p1": float(np.percentile(candidate_luma, 1)),
        "eight_bit_pixels_changed_percent": float(100.0 * np.mean(np.any(a8 != b8, axis=-1))),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    families = []
    for dr, dg, db, width_scale in product((-10.0, 0.0, 10.0), repeat=4):
        centres = BASE_CENTRES + np.array([dr, dg, db], dtype=np.float32)
        sigmas = BASE_SIGMAS * (1.0 + width_scale / 50.0)
        families.append(evaluate_family(centres, sigmas))

    baseline = evaluate_family(BASE_CENTRES, BASE_SIGMAS)
    best_fit = min(families, key=lambda row: row["holdout_rms_density"])
    best_conditioned = min(families, key=lambda row: row["matrix_max_singular"])
    worst_fit = max(families, key=lambda row: row["holdout_rms_density"])

    with (OUTPUT / "observer_sweep.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "centres_nm", "sigmas_nm", "holdout_rms_density",
                "holdout_max_abs_density", "neutral_max_abs_density",
                "matrix_max_singular", "matrix_condition", "matrix_max_abs_coefficient",
            ],
        )
        writer.writeheader()
        for row in families:
            writer.writerow({name: row[name] for name in writer.fieldnames})

    # The physical 5279 -> 2383 printer exposure integration has its own lamp
    # and print-stock sensitivities.  Verify the scanner observer monkeypatch
    # cannot alter that branch's input density calculation.
    _, physical_check_records = calibration_sets()
    physical_check_total = physical_check_records + emulsion.SENSITO_DMIN_RGB
    physical_print_before = emulsion.negative_total_printer_density_from_record_density(
        physical_check_total
    )

    raw = decode_frame()
    baseline_frame = render_scan(raw, BASE_CENTRES, BASE_SIGMAS)
    candidate_centres = np.array(best_fit["centres_nm"], dtype=np.float32)
    candidate_sigmas = np.array(best_fit["sigmas_nm"], dtype=np.float32)
    candidate_frame = render_scan(raw, candidate_centres, candidate_sigmas)
    physical_print_after = emulsion.negative_total_printer_density_from_record_density(
        physical_check_total
    )

    result = {
        "question": "Can a bounded period-telecine spectral family be uniquely preferred by six-colour separation and neutral-density constraints?",
        "documented_boundary": "DFT publishes broad-spectrum xenon illumination, RGB beam splitting, three 2048-pixel CCD arrays, optical film matching and RGB primary correction, but not detector response curves.",
        "family_definition": {
            "centre_grid_nm": "Kodak-patent visual peaks 620/540/470, independently perturbed by -10/0/+10 nm",
            "width_grid": "V21 Gaussian sigmas 52/44/38 nm scaled by 0.8/1.0/1.2",
            "family_count": len(families),
        },
        "calibration": "3x3 through-origin masking matrix fit on six CMY directions plus neutral, matching the stock-specific telecine correction operation described in EP1309188A2.",
        "baseline": baseline,
        "best_fit": best_fit,
        "best_conditioned": best_conditioned,
        "worst_fit": worst_fit,
        "ranges": {
            key: [float(min(row[key] for row in families)), float(max(row[key] for row in families))]
            for key in (
                "holdout_rms_density", "holdout_max_abs_density", "neutral_max_abs_density",
                "matrix_max_singular", "matrix_condition", "matrix_max_abs_coefficient",
            )
        },
        "frame_ab": {
            "input": str(INPUT),
            "decode": "12-bit ProRes RAW via AVFoundation extended-linear BT.2020 float32",
            "frame": FRAME_INDEX,
            "dimensions": [TEST_WIDTH, TEST_HEIGHT],
            "exposure_stops": EXPOSURE_STOPS,
            "candidate": "lowest synthetic holdout RMS family; diagnostic only, not a physical Spirit identification",
            "controlled_variables": "Only the broad period-telecine response changes. RAW decode, Panasonic transform, exposure, stochastic seed, dye-cloud formation, DIR, Cineon mapping, Blu-ray finish and all grain parameters are fixed. The 2383 optical path is not called or changed.",
            "metrics": frame_metrics(baseline_frame, candidate_frame),
        },
        "physical_2383_branch_check": {
            "scope": "5279 transmission through printer-lamp/2383 record sensitivities, before the provisional H-61 display trim",
            "max_abs_density_delta": float(np.max(np.abs(physical_print_after - physical_print_before))),
            "note": "The physical optical-print calculation is independent. V21's later H-61 hue trim still uses a provisional Spirit reference, so a production scanner change would require revalidation or a measured 5279/2383 target.",
        },
    }
    (OUTPUT / "observer_sweep_metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
