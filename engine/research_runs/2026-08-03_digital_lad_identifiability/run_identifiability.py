"""Research-only identifiability test for a 2383 log-exposure interimage matrix.

Kodak H-387 publishes a neutral Digital LAD scale and the official DPX image
contains six saturated input patches, but neither source publishes projected
Lab measurements for those patches.  US 8,654,192 places a 3x3 matrix around
the LAD exposure and says it must be fitted to DPX/theatre-Lab pairs including
saturated hues.  This script asks whether neutral LAD data alone identify that
matrix.  Production code and formal V21 outputs are never modified.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT = ROOT / "experiments" / "emulsion_reconstruction"
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(EXPERIMENT / "src"))
import emulsion_experiment as emulsion


INPUT = Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV")
DECODER = Path("/tmp/prores_raw_float_decode")
FRAME_INDEX = 144
SOURCE_WIDTH = 5760
SOURCE_HEIGHT = 4320
TEST_WIDTH = 1440
TEST_HEIGHT = 1080
EXPOSURE_STOPS = 0.45
LUMA_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)

DIGITAL_LAD_URL = (
    "https://www.kodak.com/content/products-zip/"
    "KODAK-Digital-LAD-Test-Image-DPX-Format.zip"
)
DIGITAL_LAD_ZIP_SHA256 = (
    "7cce3ca613ba36b97e9c5229631fd42c30fca49a5c1fb6695aa7a677df2ec0ad"
)
DIGITAL_LAD_2K_SHA256 = (
    "eae1f09586567bbf20f825df1911b0e0348c047138bd84fdd9c63ee1b789dddb"
)
H387_URL = (
    "https://www.kodak.com/content/products-brochures/Film/"
    "Users-Guide-and-Digital-Recorder-Calibration-and-Aims-H-387.pdf"
)
PATENT_URL = "https://patents.google.com/patent/US8654192B2/en"

# Sampled directly from the official 2048x1556 10-bit DPX, in displayed order.
PATCH_NAMES = ("red", "green", "blue", "cyan", "magenta", "yellow")
DIGITAL_LAD_PATCH_CODES = np.array(
    [
        [700, 93, 93],
        [93, 700, 93],
        [93, 93, 700],
        [93, 700, 700],
        [700, 93, 700],
        [700, 700, 93],
    ],
    dtype=np.float64,
)
H387_NEUTRAL_CODES = np.array(
    [0, 22, 95, 200, 445, 520, 685, 800, 900, 968, 1000, 1023],
    dtype=np.float64,
)
LAD_CODE = 445.0
DPX_DENSITY_PER_CODE = 0.002
KODAK_2383_LAD_STATUS_A = np.array([1.09, 1.06, 1.03], dtype=np.float64)

# The patent describes a coordinate search whose initial matrix increment may
# be 0.08.  These two bounded cyclic perturbations use that increment, have
# row sums exactly one, and are deliberately not claimed as 2383 measurements.
# They are counterexamples: both preserve every neutral DPX triplet but predict
# different saturated colours.
MATRICES = {
    "identity": np.eye(3, dtype=np.float64),
    "clockwise_008": np.array(
        [[0.92, 0.08, 0.00], [0.00, 0.92, 0.08], [0.08, 0.00, 0.92]],
        dtype=np.float64,
    ),
    "counterclockwise_008": np.array(
        [[0.92, 0.00, 0.08], [0.08, 0.92, 0.00], [0.00, 0.08, 0.92]],
        dtype=np.float64,
    ),
}

ORIGINAL_RAW_PRINT = emulsion._raw_print_2383_density_from_negative
ORIGINAL_PRINT = emulsion.print_2383_density_from_negative
ORIGINAL_VIEW = emulsion.neutralize_2383_projected_gray_scale


def json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.astype(float).tolist()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else "infinite (bit-identical)"
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def decode_frame() -> np.ndarray:
    expected = SOURCE_WIDTH * SOURCE_HEIGHT * 3 * 4
    result = subprocess.run(
        [str(DECODER), str(INPUT), str(FRAME_INDEX), "1"],
        check=True,
        stdout=subprocess.PIPE,
    )
    if len(result.stdout) != expected:
        raise RuntimeError(f"decoder returned {len(result.stdout)} bytes; expected {expected}")
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(
        SOURCE_HEIGHT, SOURCE_WIDTH, 3
    )
    return cv2.resize(raw, (TEST_WIDTH, TEST_HEIGHT), interpolation=cv2.INTER_AREA)


def reset_print_shaper_only() -> None:
    # A lab would rebalance the neutral scale after changing an interimage
    # matrix.  All later V21 viewing and H-61 colour-trim caches stay fixed.
    emulsion._PRINT_2383_NEUTRAL_SHAPERS = None


def raw_print_with_matrix(
    negative_density_rgb: np.ndarray, matrix: np.ndarray
) -> np.ndarray:
    neutral_negative = emulsion.negative_total_printer_density(
        np.array([0.18, 0.18, 0.18], dtype=np.float32)
    )
    lad_log_exposure = np.array(
        [
            emulsion._inverse_2383_density(
                channel, float(emulsion.PRINT_2383_LAD_DENSITY)
            )
            for channel in range(3)
        ],
        dtype=np.float32,
    )
    printer_log_light = neutral_negative + lad_log_exposure
    captured = printer_log_light - negative_density_rgb
    adjusted = (
        np.einsum(
            "ij,...j->...i",
            matrix.astype(np.float32),
            captured - lad_log_exposure,
        )
        + lad_log_exposure
    )
    density = np.empty_like(adjusted, dtype=np.float32)
    for channel in range(3):
        density[..., channel] = np.interp(
            adjusted[..., channel],
            emulsion.PRINT_2383_LOG_EXPOSURE,
            emulsion.PRINT_2383_DENSITY_RGB[channel],
        ).astype(np.float32)
    return density


def set_matrix(matrix: np.ndarray) -> None:
    emulsion._raw_print_2383_density_from_negative = (
        lambda negative_density_rgb: raw_print_with_matrix(
            negative_density_rgb, matrix
        )
    )
    emulsion.print_2383_density_from_negative = ORIGINAL_PRINT
    emulsion.neutralize_2383_projected_gray_scale = ORIGINAL_VIEW
    reset_print_shaper_only()


def render(raw: np.ndarray, look: str) -> np.ndarray:
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
    baseline_u8 = to_srgb_u8(baseline)
    candidate_u8 = to_srgb_u8(candidate)
    if save_images:
        save_rgb(OUTPUT / f"baseline_{name}.png", baseline_u8)
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


def dpx_log_exposure(code_rgb: np.ndarray, lad_exposure: np.ndarray) -> np.ndarray:
    return (
        lad_exposure
        + (LAD_CODE - np.asarray(code_rgb, dtype=np.float64))
        * DPX_DENSITY_PER_CODE
    )


def adjust_about_lad(
    captured: np.ndarray, matrix: np.ndarray, lad_exposure: np.ndarray
) -> np.ndarray:
    return np.einsum("ij,...j->...i", matrix, captured - lad_exposure) + lad_exposure


def synthetic_patch_gate() -> dict[str, object]:
    lad_exposure = np.array(
        [
            emulsion._inverse_2383_density(channel, KODAK_2383_LAD_STATUS_A[channel])
            for channel in range(3)
        ],
        dtype=np.float64,
    )
    neutral_triplets = np.repeat(H387_NEUTRAL_CODES[:, None], 3, axis=1)
    neutral_captured = dpx_log_exposure(neutral_triplets, lad_exposure)
    patch_captured = dpx_log_exposure(DIGITAL_LAD_PATCH_CODES, lad_exposure)
    models: dict[str, object] = {}
    patch_labs: dict[str, np.ndarray] = {}
    for name, matrix in MATRICES.items():
        adjusted_neutral = adjust_about_lad(neutral_captured, matrix, lad_exposure)
        adjusted_patch = adjust_about_lad(patch_captured, matrix, lad_exposure)
        density = np.empty_like(adjusted_patch)
        for channel in range(3):
            density[:, channel] = np.interp(
                adjusted_patch[:, channel],
                emulsion.PRINT_2383_LOG_EXPOSURE,
                emulsion.PRINT_2383_DENSITY_RGB[channel],
            )
        projected = emulsion.apply_2383_projection_lut(
            emulsion.apply_2383_callier_density(density[None, ...].astype(np.float32))
        )[0]
        lab = emulsion.linear_rec709_to_oklab(np.maximum(projected[None, ...], 0.0))[0]
        patch_labs[name] = lab.astype(np.float64)
        models[name] = {
            "matrix": matrix,
            "row_sums": np.sum(matrix, axis=1),
            "determinant": float(np.linalg.det(matrix)),
            "neutral_log_exposure_max_abs_error": float(
                np.max(np.abs(adjusted_neutral - neutral_captured))
            ),
            "digital_lad_patch_adjusted_log_exposure": adjusted_patch,
            "digital_lad_patch_status_a_density": density,
            "digital_lad_patch_projected_oklab": lab,
        }
    pair_delta = np.linalg.norm(
        patch_labs["clockwise_008"] - patch_labs["counterclockwise_008"],
        axis=1,
    )
    exposure_pair_delta = np.abs(
        np.asarray(
            models["clockwise_008"]["digital_lad_patch_adjusted_log_exposure"]
        )
        - np.asarray(
            models["counterclockwise_008"]["digital_lad_patch_adjusted_log_exposure"]
        )
    )
    return {
        "lad_log_exposure_rgb": lad_exposure,
        "h387_neutral_codes": H387_NEUTRAL_CODES,
        "official_six_patch_codes_rgb": DIGITAL_LAD_PATCH_CODES,
        "models": models,
        "clockwise_vs_counterclockwise_patch_oklab_delta_e": pair_delta,
        "clockwise_vs_counterclockwise_patch_oklab_delta_e_mean": float(
            np.mean(pair_delta)
        ),
        "clockwise_vs_counterclockwise_patch_oklab_delta_e_max": float(
            np.max(pair_delta)
        ),
        "clockwise_vs_counterclockwise_log_exposure_max_abs": float(
            np.max(exposure_pair_delta)
        ),
    }


def save_patch_plot(gate: dict[str, object]) -> None:
    delta = np.asarray(gate["clockwise_vs_counterclockwise_patch_oklab_delta_e"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), constrained_layout=True)
    colors = ("#c7372f", "#45934b", "#3857a5", "#29a9af", "#ad3ca7", "#c5b92c")
    axes[0].bar(PATCH_NAMES, delta, color=colors)
    axes[0].set(
        title="Same neutral LAD, different saturated predictions",
        ylabel="OKLab distance (model vs model)",
    )
    axes[0].tick_params(axis="x", rotation=30)
    axes[0].grid(axis="y", alpha=0.2)
    neutral_errors = [
        gate["models"][name]["neutral_log_exposure_max_abs_error"]
        for name in MATRICES
    ]
    axes[1].bar(tuple(MATRICES), neutral_errors, color=("#777", "#b06d23", "#684b9e"))
    axes[1].set(
        title="All models reproduce every H-387 neutral code",
        ylabel="Maximum log-exposure error",
    )
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].set_ylim(0.0, max(1e-12, float(np.max(neutral_errors)) * 1.2))
    axes[1].grid(axis="y", alpha=0.2)
    fig.savefig(OUTPUT / "digital_lad_identifiability.png", dpi=180)
    plt.close(fig)


def cache_baseline_calibrations() -> dict[str, object]:
    return {
        "view_neutral": emulsion._PRINT_2383_VIEW_NEUTRAL_TABLE,
        "h61_colour": dict(emulsion._PRINT_2383_H61_COLOUR_DELTA_LUTS),
        "monitor_delta": emulsion._PRINT_2383_MONITOR_DELTA_LUT,
    }


def restore_baseline_calibrations(caches: dict[str, object]) -> None:
    emulsion._PRINT_2383_VIEW_NEUTRAL_TABLE = caches["view_neutral"]
    emulsion._PRINT_2383_H61_COLOUR_DELTA_LUTS = dict(caches["h61_colour"])
    emulsion._PRINT_2383_MONITOR_DELTA_LUT = caches["monitor_delta"]


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not INPUT.is_file() or not DECODER.is_file():
        raise FileNotFoundError("RAW source or AVFoundation float decoder is missing")

    patch_gate = synthetic_patch_gate()
    save_patch_plot(patch_gate)

    raw = decode_frame()
    emulsion._raw_print_2383_density_from_negative = ORIGINAL_RAW_PRINT
    emulsion.print_2383_density_from_negative = ORIGINAL_PRINT
    emulsion.neutralize_2383_projected_gray_scale = ORIGINAL_VIEW
    reset_print_shaper_only()
    baseline_projection = render(raw, "2383_projection_monitor")
    baseline_scan = render(raw, "cineon_bluray")
    baseline_caches = cache_baseline_calibrations()

    projections: dict[str, np.ndarray] = {}
    scans: dict[str, np.ndarray] = {}
    matrix_vs_v21: dict[str, object] = {}
    scan_isolation: dict[str, object] = {}
    for name in ("clockwise_008", "counterclockwise_008"):
        set_matrix(MATRICES[name])
        restore_baseline_calibrations(baseline_caches)
        projections[name] = render(raw, "2383_projection_monitor")
        scans[name] = render(raw, "cineon_bluray")
        matrix_vs_v21[name] = compare(
            f"{name}_vs_v21_frame{FRAME_INDEX}",
            baseline_projection,
            projections[name],
            save_images=False,
        )
        scan_isolation[name] = compare(
            f"{name}_scan_isolation_frame{FRAME_INDEX}",
            baseline_scan,
            scans[name],
            save_images=False,
        )

    pair_metrics = compare(
        f"clockwise_vs_counterclockwise_frame{FRAME_INDEX}",
        projections["clockwise_008"],
        projections["counterclockwise_008"],
        save_images=True,
    )

    result = {
        "question": (
            "Do Kodak H-387's neutral Digital LAD scale and the official Digital LAD "
            "image uniquely identify the LAD-anchored 3x3 2383 log-exposure "
            "interimage matrix described by US8654192B2?"
        ),
        "sources": {
            "kodak_h387": {
                "url": H387_URL,
                "pages": "1-5; neutral recorder aims and 445/445/445 LAD patch",
            },
            "kodak_digital_lad_dpx": {
                "url": DIGITAL_LAD_URL,
                "zip_sha256": DIGITAL_LAD_ZIP_SHA256,
                "dpx_2048_sha256": DIGITAL_LAD_2K_SHA256,
                "observation": (
                    "The official 10-bit DPX contains six saturated patches at "
                    "93/700 code combinations, but Kodak publishes no corresponding "
                    "processed-2383 or theatre-Lab aim values."
                ),
            },
            "us8654192b2": {
                "url": PATENT_URL,
                "paragraphs": "Figure 14 discussion, especially 575-588 in Google Patents text",
                "fact": (
                    "The matrix is applied in log exposure about LAD and fitted to "
                    "measured DPX/theatre-Lab pairs distributed across the input "
                    "space, including saturated hues."
                ),
            },
        },
        "input": str(INPUT),
        "input_probe": {
            "codec": "ProRes RAW HQ",
            "dimensions": [SOURCE_WIDTH, SOURCE_HEIGHT],
            "bits_per_raw_sample": 12,
        },
        "decode": "AVFoundation extended-linear BT.2020 float32; resized by area to 1440x1080",
        "frame": FRAME_INDEX,
        "exposure_stops": EXPOSURE_STOPS,
        "seed_policy": "V21 deterministic frame-index seed; identical within all A/B renders",
        "controlled_variables": (
            "Only a research-only 3x3 matrix in 2383 log exposure changes. The "
            "neutral 1D shaper is re-solved as a mandatory lab rebalance; the "
            "baseline V21 projection-view, H-61 colour-trim and monitor caches are "
            "held fixed. RAW decode, 5279 development/DIR/dye-cloud grain, printer "
            "light, 2383 curves/dyes, Callier term, xenon observer, flare and scan "
            "branch remain fixed."
        ),
        "model_assumption_boundary": (
            "The two 0.08 cyclic matrices are counterexamples chosen from the "
            "patent's stated initial search increment; neither is claimed as a "
            "measurement of 2383."
        ),
        "digital_lad_identifiability_gate": patch_gate,
        "raw_frame_matrix_vs_v21": matrix_vs_v21,
        "raw_frame_clockwise_vs_counterclockwise": pair_metrics,
        "scan_branch_isolation": scan_isolation,
        "release_gate": {
            "neutral_data_identifies_matrix": False,
            "measured_saturated_dpx_to_theatre_lab_target_available": False,
            "decision": "reject both matrices; retain V21",
            "reason": (
                "Multiple bounded matrices reproduce every published neutral code "
                "exactly yet disagree on the official saturated inputs and the same "
                "RAW frame. Without measured output targets there is no evidence to "
                "choose one, so releasing either would be subjective colour drift."
            ),
        },
    }
    metrics_path = OUTPUT / "metrics.json"
    metrics_path.write_text(
        json.dumps(json_safe(result), ensure_ascii=False, indent=2, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )

    emulsion._raw_print_2383_density_from_negative = ORIGINAL_RAW_PRINT
    emulsion.print_2383_density_from_negative = ORIGINAL_PRINT
    emulsion.neutralize_2383_projected_gray_scale = ORIGINAL_VIEW
    reset_print_shaper_only()

    for path in (
        Path(__file__),
        metrics_path,
        OUTPUT / "digital_lad_identifiability.png",
        OUTPUT / f"ab_clockwise_vs_counterclockwise_frame{FRAME_INDEX}.png",
        OUTPUT / f"difference_x12_clockwise_vs_counterclockwise_frame{FRAME_INDEX}.png",
    ):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{digest}  {path}")


if __name__ == "__main__":
    main()
