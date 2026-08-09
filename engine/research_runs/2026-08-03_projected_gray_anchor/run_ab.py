"""Controlled 2383 projected-gray anchor experiment.

The preceding Status-A trajectory run found that Kodak's documented
1.09/1.06/1.03 LAD vector can be preserved in a proportional analytical-dye
trajectory, but it deliberately left V21's later projected-gray correction
unchanged.  This research-only script isolates that later stage.

Four variants are compared:

1. V21: equal 1.00 Status-A print aim and equal-density view correction.
2. Kodak LAD proportional trajectory with V21's equal-density view correction.
3. Kodak LAD proportional trajectory with no post-spectral neutral correction.
4. Kodak LAD proportional trajectory with a view correction calibrated on
   scalar multiples of the official LAD vector.

Variant 4 is a model inference, not a measured 5279-to-2383 gray strip.  It is
tested because Kodak sources distinguish Status-A density from visual neutral
density and place viewing-light conversion after analytical dye amount.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT = ROOT / "experiments" / "emulsion_reconstruction"
sys.path.insert(0, str(EXPERIMENT / "src"))
import emulsion_experiment as emulsion


PREVIOUS_SCRIPT = (
    EXPERIMENT
    / "research_runs"
    / "2026-08-03_status_a_trajectory"
    / "run_ab.py"
)
spec = importlib.util.spec_from_file_location("status_a_trajectory_ab", PREVIOUS_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {PREVIOUS_SCRIPT}")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)


OUTPUT = Path(__file__).resolve().parent
previous.OUTPUT = OUTPUT
ORIGINAL_VIEW_NEUTRALIZER = emulsion.neutralize_2383_projected_gray_scale
ORIGINAL_RAW_PRINT = emulsion._raw_print_2383_density_from_negative
ORIGINAL_PRINT_DENSITY = emulsion.print_2383_density_from_negative
KODAK_AIM = previous.KODAK_AIM
LUMA_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

_LAD_VIEW_TABLE: tuple[np.ndarray, np.ndarray] | None = None


def reset_caches() -> None:
    global _LAD_VIEW_TABLE
    previous.reset_caches()
    _LAD_VIEW_TABLE = None


def identity_view_neutralizer(projected: np.ndarray) -> np.ndarray:
    return np.maximum(np.asarray(projected, dtype=np.float32), 0.0)


def build_lad_trajectory_view_table() -> tuple[np.ndarray, np.ndarray]:
    """Build RGB neutral factors on scalar multiples of Kodak's LAD vector.

    The proportional trajectory is the same inference tested at the print
    density stage in the preceding run.  This table only asks whether the
    downstream spectral/view correction should use that trajectory instead of
    V21's equal Status-A density axis.
    """
    maximum_scale = float(emulsion.PRINT_2383_DMAX / np.max(KODAK_AIM))
    scale = np.linspace(0.0, maximum_scale, 257, dtype=np.float32)
    status_a = scale[:, None] * KODAK_AIM[None, :]
    status_a = emulsion.apply_2383_callier_density(status_a[None, ...])
    rgb = np.maximum(emulsion.apply_2383_projection_lut(status_a)[0], 1e-8)
    luma = np.einsum("...c,c->...", rgb, LUMA_WEIGHTS)
    factors = luma[:, None] / rgb
    order = np.argsort(luma)
    return (
        luma[order].astype(np.float32),
        np.clip(factors[order], 0.35, 2.50).astype(np.float32),
    )


def lad_trajectory_view_neutralizer(projected: np.ndarray) -> np.ndarray:
    global _LAD_VIEW_TABLE
    if _LAD_VIEW_TABLE is None:
        _LAD_VIEW_TABLE = build_lad_trajectory_view_table()
    luma_axis, factor_table = _LAD_VIEW_TABLE
    source = np.maximum(np.asarray(projected, dtype=np.float32), 0.0)
    luma = np.einsum("...c,c->...", source, LUMA_WEIGHTS)
    corrected = np.empty_like(source)
    for channel in range(3):
        factor = np.interp(luma, luma_axis, factor_table[:, channel])
        corrected[..., channel] = source[..., channel] * factor
    return np.maximum(corrected, 0.0).astype(np.float32)


MODES = {
    "v21_equal": (
        previous.V21_AIM,
        ORIGINAL_PRINT_DENSITY,
        ORIGINAL_VIEW_NEUTRALIZER,
    ),
    "kodak_ad_v21_view": (
        KODAK_AIM,
        previous.analytical_dye_print_density,
        ORIGINAL_VIEW_NEUTRALIZER,
    ),
    "kodak_ad_no_view": (
        KODAK_AIM,
        previous.analytical_dye_print_density,
        identity_view_neutralizer,
    ),
    "kodak_ad_lad_view": (
        KODAK_AIM,
        previous.analytical_dye_print_density,
        lad_trajectory_view_neutralizer,
    ),
}


def set_mode(mode: str) -> None:
    aim, print_shaper, view_neutralizer = MODES[mode]
    emulsion._raw_print_2383_density_from_negative = (
        lambda negative_density_rgb: previous.raw_print_with_aim(
            negative_density_rgb, aim
        )
    )
    emulsion.print_2383_density_from_negative = print_shaper
    emulsion.neutralize_2383_projected_gray_scale = view_neutralizer
    reset_caches()


def render(raw: np.ndarray, mode: str, look: str) -> np.ndarray:
    set_mode(mode)
    return emulsion.reconstruct_through_emulsion(
        raw,
        previous.FRAME_INDEX,
        grain_scale=1.0,
        oversample=1,
        exposure_stops=previous.EXPOSURE_STOPS,
        look=look,
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )


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
    spectral_lab = emulsion.linear_rec709_to_oklab(spectral[None, ...])[0]
    corrected_lab = emulsion.linear_rec709_to_oklab(corrected[None, ...])[0]

    lad_negative = emulsion.negative_total_printer_density(
        np.array([0.18, 0.18, 0.18], dtype=np.float32)
    )
    lad_status_a = emulsion.print_2383_density_from_negative(lad_negative)
    lad_spectral = np.maximum(
        emulsion.apply_2383_projection_lut(
            emulsion.apply_2383_callier_density(lad_status_a.reshape(1, 1, 3))
        )[0, 0],
        0.0,
    )
    lad_corrected = emulsion.neutralize_2383_projected_gray_scale(
        lad_spectral.reshape(1, 1, 3)
    )[0, 0]
    lad_lab = emulsion.linear_rec709_to_oklab(lad_corrected.reshape(1, 1, 3))[0, 0]
    return {
        "probe_note": "Six representative stops, not measured H-61 patch exposures.",
        "probe_stops_from_18_percent": probe_stops.astype(float).tolist(),
        "status_a": status_a.astype(float).tolist(),
        "spectral_rgb": spectral.astype(float).tolist(),
        "corrected_rgb": corrected.astype(float).tolist(),
        "spectral_oklab_chroma": np.linalg.norm(
            spectral_lab[:, 1:3], axis=1
        ).astype(float).tolist(),
        "corrected_oklab_chroma": np.linalg.norm(
            corrected_lab[:, 1:3], axis=1
        ).astype(float).tolist(),
        "corrected_oklab_chroma_mean": float(
            np.mean(np.linalg.norm(corrected_lab[:, 1:3], axis=1))
        ),
        "corrected_oklab_chroma_max": float(
            np.max(np.linalg.norm(corrected_lab[:, 1:3], axis=1))
        ),
        "lad_status_a": np.asarray(lad_status_a).astype(float).tolist(),
        "lad_spectral_rgb": lad_spectral.astype(float).tolist(),
        "lad_corrected_rgb": lad_corrected.astype(float).tolist(),
        "lad_corrected_rgb_span": float(np.ptp(lad_corrected)),
        "lad_corrected_oklab_chroma": float(np.linalg.norm(lad_lab[1:3])),
    }


def patch_gate(mode: str) -> dict[str, object]:
    set_mode(mode)
    return _patch_gate_current()


def _patch_gate_current() -> dict[str, object]:
    values = np.array(
        [
            [0.18, 0.18, 0.18],
            [0.45, 0.06, 0.04],
            [0.05, 0.38, 0.08],
            [0.035, 0.08, 0.46],
            [0.52, 0.42, 0.05],
            [0.42, 0.05, 0.38],
            [0.04, 0.39, 0.42],
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
        "mean_absolute_hue_delta_degrees_excluding_neutral": float(
            np.mean(hue_delta[1:])
        ),
        "neutral_projection_rgb_span": float(np.ptp(projection[0])),
    }


def json_safe(value: object) -> object:
    """Keep the metrics artifact strict JSON even for bit-identical PSNR."""
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not np.isfinite(value):
        return "infinite (bit-identical)"
    return value


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = previous.decode_frame()
    renders = {
        mode: render(raw, mode, "2383_projection_monitor") for mode in MODES
    }
    baseline_scan = render(raw, "v21_equal", "cineon_bluray")
    candidate_scan = render(raw, "kodak_ad_lad_view", "cineon_bluray")

    baseline_u8 = previous.to_srgb_u8(renders["v21_equal"])
    previous.save_rgb(OUTPUT / "baseline_v21_equal.png", baseline_u8)

    result = {
        "question": "Should V21's post-spectral gray correction use equal Status-A densities, no correction, or a trajectory through Kodak's 1.09/1.06/1.03 visual-neutral LAD vector?",
        "input": str(previous.INPUT),
        "decode": "12-bit ProRes RAW via AVFoundation extended-linear BT.2020 float32",
        "frame": previous.FRAME_INDEX,
        "dimensions": [previous.TEST_WIDTH, previous.TEST_HEIGHT],
        "exposure_stops": previous.EXPOSURE_STOPS,
        "seed_policy": "V21 deterministic frame-index seed; identical for every variant",
        "model_boundary": "The LAD-proportional view trajectory is an inference. Kodak supplies the LAD anchor and six-patch neutrality criterion, not measured 5279-to-2383 off-LAD Status-A vectors.",
        "controlled_variables": "Within the three Kodak-AD modes, only the post-spectral projected-gray correction varies. The V21 comparison also includes the preceding official-LAD proportional print-density candidate. RAW decode, +0.45 stop, 5279 H-D/chemistry/DIR/morphology/seed, 3200 K printing, 2383 curves/dyes, Callier term, xenon SPD, H-61 colour guard, monitor adaptation and scan branch remain fixed.",
        "view_gate": {mode: view_gate(mode) for mode in MODES},
        "patch_gate": {mode: patch_gate(mode) for mode in MODES},
        "frame_ab_vs_v21": {
            mode: previous.compare(mode, renders["v21_equal"], renders[mode])
            for mode in MODES
            if mode != "v21_equal"
        },
        "view_stage_isolation_vs_kodak_ad_v21_view": {
            mode: previous.compare(
                f"view_isolation_{mode}",
                renders["kodak_ad_v21_view"],
                renders[mode],
            )
            for mode in ("kodak_ad_no_view", "kodak_ad_lad_view")
        },
        "scan_branch_isolation": previous.compare(
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
