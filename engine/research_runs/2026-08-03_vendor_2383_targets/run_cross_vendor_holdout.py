#!/usr/bin/env python3
"""Hold out six chromatic directions against independent 2383 vendor looks.

The candidate fixes two distinct operations that V21 conflated:
1. Status-A integral print density is converted to analytical CMY dye amount.
2. A LAD-anchored 3x3 log-exposure interimage matrix is applied before the
   three 2383 characteristic curves.

The matrix was identified only from the mid-gray local Jacobian consensus.
Six finite chromatic excursions are therefore a genuine nonlinear holdout.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from analyze_vendor_luts import SOURCES, load_cube, neutral_for_output, sample_3d
import run_real_frame_vendor_ab as real_frame_ab


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src" / "emulsion_experiment.py"
STATUS_METRICS = (
    ROOT
    / "research_runs"
    / "2026-08-03_status_a_spectral_product"
    / "metrics.json"
)
STATUS_SCRIPT = STATUS_METRICS.parent / "run_holdout.py"
VENDOR_LOCAL_METRICS = HERE / "metrics.json"


def load_emulsion(name: str):
    spec = importlib.util.spec_from_file_location(name, SRC)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SRC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


baseline = load_emulsion("emulsion_vendor_baseline")
candidate = load_emulsion("emulsion_vendor_candidate")

# Cross-vendor median at the neutral midtone. Order per row is the two
# off-diagonal entries. It was computed from Resolve D55/D60/D65, Adobe,
# FilmVision SD1/2/3, and BMD's ACES LMT (at linear 18%).
TARGET_LOCAL_NORMALIZED_JACOBIAN = np.array(
    [[1.0, 0.029, -0.046], [0.153, 1.0, 0.087], [0.037, 0.213, 1.0]],
    dtype=np.float64,
)

# LAD-anchored log-exposure matrix obtained by iterating the analytical local
# chain until its held-in mid-gray Jacobian matched the cross-vendor median.
# This is not claimed as a Kodak-published matrix; the six finite patches below
# are kept out of that identification.
PRINT_INTERIMAGE_MATRIX = np.array(
    [
        [1.4105, -0.9566, 0.9152],
        [0.4127, 0.6943, -0.2324],
        [-0.5640, 0.6093, 0.8425],
    ],
    dtype=np.float64,
)


def build_v21_projection_lut(e, size: int = 25) -> np.ndarray:
    """Archive V21's direct Status-A-as-CMY projection operation in the test."""
    axis = np.linspace(0.0, e.PRINT_2383_DMAX, size, dtype=np.float64)
    cyan, magenta, yellow = np.meshgrid(axis, axis, axis, indexing="ij")
    cmy = np.stack([cyan, magenta, yellow], axis=-1).reshape(-1, 3)
    cmf = e._cie_1931_xyz_approx(e.PRINT_DYE_WAVELENGTHS_NM).astype(np.float64)
    weighted_cmf = e.KODAK_XENON_PROJECTOR_RELATIVE_SPD[:, None] * cmf
    white_xyz = np.sum(weighted_cmf, axis=0)
    source_white = white_xyz / white_xyz[1]
    d65_xyz = np.array([0.95047, 1.0, 1.08883], dtype=np.float64)
    bradford = np.array(
        [[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]],
        dtype=np.float64,
    )
    adaptation = (
        np.linalg.inv(bradford)
        @ np.diag((bradford @ d65_xyz) / (bradford @ source_white))
        @ bradford
    )
    spectral_density = np.clip(
        np.einsum(
            "...c,wc->...w",
            cmy,
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY.astype(np.float64),
        ),
        0.0,
        16.0,
    )
    xyz = np.einsum("...w,wc->...c", 10.0 ** (-spectral_density), weighted_cmf)
    xyz = np.einsum("...c,dc->...d", xyz / white_xyz[1], adaptation)
    rgb = np.einsum("...c,dc->...d", xyz, e.XYZ_D65_TO_REC709)
    return rgb.reshape(size, size, size, 3).astype(np.float32)


def install_v21_baseline() -> None:
    baseline.PRINT_2383_INTERIMAGE_MATRIX = np.eye(3, dtype=np.float32)
    baseline._PRINT_2383_PROJECTION_LUT = build_v21_projection_lut(baseline)
    baseline._PRINT_2383_NEUTRAL_SHAPERS = None
    baseline._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    baseline._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    baseline._PRINT_2383_MONITOR_DELTA_LUT = None


def baseline_v21_monitor(total: np.ndarray) -> np.ndarray:
    density = total[None, None]
    physical = baseline.render_2383_projection_from_record_density(
        density, include_reference_flare=True
    )
    scan = baseline.finish_cineon_scan_for_bluray(
        baseline.render_cineon_scan_master_from_record_density(density)
    )
    return baseline.match_2383_projection_to_rec709_monitor(physical, scan)[0, 0]


def build_analytical_projection_lut(e, size: int = 25) -> np.ndarray:
    status_spec = importlib.util.spec_from_file_location(
        "status_a_vendor_holdout", STATUS_SCRIPT
    )
    if status_spec is None or status_spec.loader is None:
        raise RuntimeError(f"cannot load {STATUS_SCRIPT}")
    status_model = importlib.util.module_from_spec(status_spec)
    status_spec.loader.exec_module(status_model)

    axis = np.linspace(0.0, e.PRINT_2383_DMAX, size, dtype=np.float64)
    amount_axis = np.linspace(0.0, 14.0, 28001, dtype=np.float64)
    analytical_axes = []
    for channel in range(3):
        separated_amount = np.zeros((amount_axis.size, 3), dtype=np.float64)
        separated_amount[:, channel] = amount_axis
        principal_status = status_model.status_a_net_density(
            separated_amount, np.ones(3)
        )[:, channel]
        analytical_axes.append(
            np.interp(
                np.maximum(axis - status_model.DMIN_RGB[channel], 0.0),
                principal_status,
                amount_axis,
            )
        )
    cyan, magenta, yellow = np.meshgrid(*analytical_axes, indexing="ij")
    analytical_cmy = np.stack([cyan, magenta, yellow], axis=-1).reshape(-1, 3)

    cmf = e._cie_1931_xyz_approx(e.PRINT_DYE_WAVELENGTHS_NM).astype(np.float64)
    weighted_cmf = (
        e.KODAK_XENON_PROJECTOR_RELATIVE_SPD.astype(np.float64)[:, None] * cmf
    )
    white_xyz = np.sum(weighted_cmf, axis=0)
    source_white = white_xyz / white_xyz[1]
    d65_xyz = np.array([0.95047, 1.0, 1.08883], dtype=np.float64)
    bradford = np.array(
        [
            [0.8951, 0.2664, -0.1614],
            [-0.7502, 1.7135, 0.0367],
            [0.0389, -0.0685, 1.0296],
        ],
        dtype=np.float64,
    )
    adaptation = (
        np.linalg.inv(bradford)
        @ np.diag((bradford @ d65_xyz) / (bradford @ source_white))
        @ bradford
    )
    spectral_density = np.clip(
        np.einsum(
            "...c,wc->...w",
            analytical_cmy,
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY.astype(np.float64),
        ),
        0.0,
        16.0,
    )
    xyz = np.einsum("...w,wc->...c", np.power(10.0, -spectral_density), weighted_cmf)
    xyz = np.einsum("...c,dc->...d", xyz / white_xyz[1], adaptation)
    rgb = np.einsum(
        "...c,dc->...d", xyz, e.XYZ_D65_TO_REC709.astype(np.float64)
    )
    return rgb.reshape(size, size, size, 3).astype(np.float32)


def install_candidate() -> None:
    candidate._PRINT_2383_PROJECTION_LUT = build_analytical_projection_lut(candidate)
    neutral_negative = candidate.negative_total_printer_density(
        np.array([0.18, 0.18, 0.18], dtype=np.float32)
    )
    aim = np.array(
        [candidate._inverse_2383_density(c, 1.0) for c in range(3)],
        dtype=np.float32,
    )
    printer_light = neutral_negative + aim

    def raw_density(negative_density_rgb: np.ndarray) -> np.ndarray:
        captured = printer_light - negative_density_rgb
        adjusted = aim + np.einsum(
            "...c,dc->...d",
            captured - aim,
            PRINT_INTERIMAGE_MATRIX,
        )
        density = np.empty_like(adjusted, dtype=np.float32)
        for channel in range(3):
            density[..., channel] = np.interp(
                adjusted[..., channel],
                candidate.PRINT_2383_LOG_EXPOSURE,
                candidate.PRINT_2383_DENSITY_RGB[channel],
            ).astype(np.float32)
        return density

    candidate._raw_print_2383_density_from_negative = raw_density
    candidate._PRINT_2383_NEUTRAL_SHAPERS = None
    candidate._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    candidate._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    candidate._PRINT_2383_MONITOR_DELTA_LUT = None


def neutral_record_density(e) -> np.ndarray:
    scene = np.full((1, 1, 3), 0.18, dtype=np.float32)
    film = e.vgamut_to_balanced_film_rgb(e.bt2020_to_panasonic_vgamut(scene))
    return e.develop_5279_record_density(e.film_records_from_rgb(film))[0, 0]


def continuous_cineon_code(e, total: np.ndarray) -> np.ndarray:
    scanner = e.scanner_density_from_total_record_density(total[None, None])[0, 0]
    gain = 0.700 / e.NEUTRAL_MID_SCANNER_DENSITY
    return (95.0 + scanner * gain / 0.002) / 1023.0


def solve_total_for_cineon(e, target: np.ndarray, initial: np.ndarray) -> np.ndarray:
    lower = e.SENSITO_DMIN_RGB.astype(np.float64) - 0.12
    upper = e.SENSITO_DMIN_RGB.astype(np.float64) + e.NEGATIVE_5279_MAX_RECORD_DENSITY

    def residual(total: np.ndarray) -> np.ndarray:
        return continuous_cineon_code(e, total.astype(np.float32)) - target

    result = least_squares(
        residual,
        initial.astype(np.float64),
        bounds=(lower, upper),
        xtol=1e-12,
        ftol=1e-12,
        gtol=1e-12,
        max_nfev=200,
        diff_step=2e-4,
    )
    if np.max(np.abs(result.fun)) > 2e-5:
        raise RuntimeError(f"Cineon inversion failed: {result.fun}")
    return result.x.astype(np.float32)


def rec709_decode(value: np.ndarray, gamma: float) -> np.ndarray:
    return np.power(np.maximum(value, 0.0), gamma)


def delta_ab(e, linear_rgb: np.ndarray, neutral_linear: np.ndarray) -> np.ndarray:
    return (
        e.linear_rec709_to_oklab(linear_rgb[None, None])[0, 0, 1:3]
        - e.linear_rec709_to_oklab(neutral_linear[None, None])[0, 0, 1:3]
    ).astype(np.float64)


def angle_degrees(vector: np.ndarray) -> float:
    return float(np.degrees(np.arctan2(vector[1], vector[0])))


def angular_distance(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def local_normalized_log_jacobian(e, total: np.ndarray, renderer) -> np.ndarray:
    step = 0.004
    output_jacobian = np.empty((3, 3), dtype=np.float64)
    cineon_jacobian = np.empty((3, 3), dtype=np.float64)
    for channel in range(3):
        plus, minus = total.copy(), total.copy()
        plus[channel] += step
        minus[channel] -= step
        output_jacobian[:, channel] = (
            np.log(np.maximum(renderer(plus), 1e-8))
            - np.log(np.maximum(renderer(minus), 1e-8))
        ) / (2.0 * step)
        cineon_jacobian[:, channel] = (
            continuous_cineon_code(e, plus)
            - continuous_cineon_code(e, minus)
        ) / (2.0 * step)
    jacobian = output_jacobian @ np.linalg.inv(cineon_jacobian)
    return jacobian / np.diag(jacobian)[:, None]


def circular_median(values: list[float]) -> float:
    candidates = np.linspace(-180.0, 180.0, 7201)
    loss = [sum(angular_distance(x, y) for y in values) for x in candidates]
    return float(candidates[int(np.argmin(loss))])


def candidate_physical(total: np.ndarray) -> np.ndarray:
    return candidate._render_2383_projection_uncalibrated(total[None, None])[0, 0]


def candidate_legacy_monitor(total: np.ndarray) -> np.ndarray:
    density = total[None, None]
    physical = candidate.render_2383_projection_from_record_density(
        density, include_reference_flare=True
    )
    scan = candidate.finish_cineon_scan_for_bluray(
        candidate.render_cineon_scan_master_from_record_density(density)
    )
    return candidate.match_2383_projection_to_rec709_monitor(physical, scan)[0, 0]


def candidate_monitor_hue_preserving(total: np.ndarray) -> np.ndarray:
    """Use the scan only for display lightness; retain physical 2383 hue/sat."""
    density = total[None, None]
    physical = candidate._render_2383_projection_uncalibrated(density)
    scan = candidate.finish_cineon_scan_for_bluray(
        candidate.render_cineon_scan_master_from_record_density(density)
    )
    scan_luma = np.einsum(
        "...c,c->...", np.maximum(scan, 0.0), [0.2126, 0.7152, 0.0722]
    )
    target_luma = np.interp(
        scan_luma,
        candidate.PRINT_MONITOR_SCAN_LUMA_ANCHORS,
        candidate.PRINT_MONITOR_TARGET_LUMA_ANCHORS,
    ).astype(np.float32)
    scaled_scan = scan * (target_luma / np.maximum(scan_luma, 1e-6))[..., None]
    target_lightness = candidate.linear_rec709_to_oklab(
        np.maximum(scaled_scan, 0.0)
    )[..., 0]
    physical_lab = candidate.linear_rec709_to_oklab(physical)
    result_lab = physical_lab.copy()
    result_lab[..., 1:3] *= (
        target_lightness / np.maximum(physical_lab[..., 0], 0.025)
    )[..., None]
    result_lab[..., 0] = target_lightness
    return candidate.compress_oklab_chroma_to_rec709(
        candidate.oklab_to_linear_rec709(result_lab)
    )[0, 0]


def candidate_monitor_physical_hue_bounded_sat(total: np.ndarray) -> np.ndarray:
    """Keep candidate 2383 hue, bound monitor saturation to the scan anchor."""
    density = total[None, None]
    physical = candidate._render_2383_projection_uncalibrated(density)
    scan = candidate.finish_cineon_scan_for_bluray(
        candidate.render_cineon_scan_master_from_record_density(density)
    )
    scan_luma = np.einsum(
        "...c,c->...", np.maximum(scan, 0.0), [0.2126, 0.7152, 0.0722]
    )
    target_luma = np.interp(
        scan_luma,
        candidate.PRINT_MONITOR_SCAN_LUMA_ANCHORS,
        candidate.PRINT_MONITOR_TARGET_LUMA_ANCHORS,
    ).astype(np.float32)
    scaled_scan = scan * (target_luma / np.maximum(scan_luma, 1e-6))[..., None]
    reference_lab = candidate.linear_rec709_to_oklab(np.maximum(scaled_scan, 0.0))
    physical_lab = candidate.linear_rec709_to_oklab(physical)
    lightness = reference_lab[..., 0]
    physical_chroma = np.linalg.norm(physical_lab[..., 1:3], axis=-1)
    reference_chroma = np.linalg.norm(reference_lab[..., 1:3], axis=-1)
    direction = physical_lab[..., 1:3] / np.maximum(
        physical_chroma[..., None], 1e-8
    )
    physical_saturation = physical_chroma / np.maximum(
        physical_lab[..., 0], 0.025
    )
    reference_saturation = reference_chroma / np.maximum(lightness, 0.025)
    saturation = 0.60 * physical_saturation + 0.40 * reference_saturation
    saturation = np.clip(
        saturation,
        0.88 * reference_saturation,
        1.18 * reference_saturation + 1e-5,
    )
    result_lab = reference_lab.copy()
    result_lab[..., 1:3] = direction * (saturation * lightness)[..., None]
    return candidate.compress_oklab_chroma_to_rec709(
        candidate.oklab_to_linear_rec709(result_lab)
    )[0, 0]


def build_neutral_monitor_curve() -> tuple[np.ndarray, np.ndarray]:
    physical_values = []
    target_values = []
    for stop in np.linspace(-12.0, 9.0, 337):
        level = 0.18 * (2.0**stop)
        scene = np.full((1, 1, 3), level, dtype=np.float32)
        film = candidate.vgamut_to_balanced_film_rgb(
            candidate.bt2020_to_panasonic_vgamut(scene)
        )
        total = candidate.develop_5279_record_density(
            candidate.film_records_from_rgb(film)
        )
        physical = candidate._render_2383_projection_uncalibrated(total)[0, 0]
        scan = candidate.finish_cineon_scan_for_bluray(
            candidate.render_cineon_scan_master_from_record_density(total)
        )[0, 0]
        physical_values.append(float(np.mean(physical)))
        scan_luma = float(np.dot(scan, [0.2126, 0.7152, 0.0722]))
        target_values.append(
            float(
                np.interp(
                    scan_luma,
                    candidate.PRINT_MONITOR_SCAN_LUMA_ANCHORS,
                    candidate.PRINT_MONITOR_TARGET_LUMA_ANCHORS,
                )
            )
        )
    order = np.argsort(physical_values)
    x = np.asarray(physical_values)[order]
    y = np.asarray(target_values)[order]
    x, unique = np.unique(x, return_index=True)
    return x.astype(np.float32), y[unique].astype(np.float32)


def candidate_monitor_channel_curve(
    total: np.ndarray, curve: tuple[np.ndarray, np.ndarray]
) -> np.ndarray:
    """Apply one neutral-derived display curve independently to R, G and B."""
    physical = candidate_physical(total)
    x, y = curve
    return np.array(
        [np.interp(physical[channel], x, y) for channel in range(3)],
        dtype=np.float32,
    )


def candidate_monitor_hybrid(
    total: np.ndarray, curve: tuple[np.ndarray, np.ndarray]
) -> np.ndarray:
    """Physical near-neutral response plus finite-colour H-61 calibration."""
    physical_view = candidate_monitor_channel_curve(total, curve)
    calibrated_view = candidate_legacy_monitor(total)
    relative_chroma = (
        np.max(physical_view) - np.min(physical_view)
    ) / max(float(np.max(physical_view)), 1e-6)
    calibrated_weight = float(candidate.smoothstep(0.02, 0.12, relative_chroma))
    physical_lab = candidate.linear_rec709_to_oklab(physical_view[None, None])
    calibrated_lab = candidate.linear_rec709_to_oklab(calibrated_view[None, None])
    result_lab = (
        (1.0 - calibrated_weight) * physical_lab
        + calibrated_weight * calibrated_lab
    )
    result = candidate.compress_oklab_chroma_to_rec709(
        candidate.oklab_to_linear_rec709(result_lab)
    )[0, 0]
    # The nonlinear principal-curve inverse becomes poorly conditioned where
    # all three records are on the clear-print shoulder. Protect only genuinely
    # neutral highlights; coloured highlights retain the physical branch.
    scan = candidate.finish_cineon_scan_for_bluray(
        candidate.render_cineon_scan_master_from_record_density(total[None, None])
    )[0, 0]
    scan_max = float(np.max(scan))
    scan_relative_chroma = (scan_max - float(np.min(scan))) / max(scan_max, 1e-6)
    scan_luma = float(np.dot(scan, [0.2126, 0.7152, 0.0722]))
    target_neutral = float(
        np.interp(
            scan_luma,
            candidate.PRINT_MONITOR_SCAN_LUMA_ANCHORS,
            candidate.PRINT_MONITOR_TARGET_LUMA_ANCHORS,
        )
    )
    neutral_highlight_weight = float(
        candidate.smoothstep(0.82, 0.94, target_neutral)
        * (1.0 - candidate.smoothstep(0.010, 0.060, scan_relative_chroma))
    )
    return (
        result * (1.0 - neutral_highlight_weight)
        + target_neutral * neutral_highlight_weight
    ).astype(np.float32)


def main() -> None:
    install_v21_baseline()
    install_candidate()
    neutral_monitor_curve = build_neutral_monitor_curve()
    d60_monitor_delta_lut = real_frame_ab.build_d60_monitor_chroma_delta_lut(
        candidate
    )
    neutral_total = neutral_record_density(candidate)
    neutral_q = continuous_cineon_code(candidate, neutral_total)
    delta = 0.060
    patch_vectors = {
        "red_axis": np.array([delta, -delta / 2, -delta / 2]),
        "cyan_axis": np.array([-delta, delta / 2, delta / 2]),
        "green_axis": np.array([-delta / 2, delta, -delta / 2]),
        "magenta_axis": np.array([delta / 2, -delta, delta / 2]),
        "blue_axis": np.array([-delta / 2, -delta / 2, delta]),
        "yellow_axis": np.array([delta / 2, delta / 2, -delta]),
    }

    totals = {
        name: solve_total_for_cineon(candidate, neutral_q + direction, neutral_total)
        for name, direction in patch_vectors.items()
    }
    renderers = {
        "v21_monitor": baseline_v21_monitor,
        "candidate_physical": candidate_physical,
        "candidate_monitor_hue_preserving": candidate_monitor_hue_preserving,
        "candidate_monitor_physical_hue_bounded_sat": candidate_monitor_physical_hue_bounded_sat,
        "candidate_monitor_channel_curve": lambda total: candidate_monitor_channel_curve(
            total, neutral_monitor_curve
        ),
        "candidate_monitor_hybrid": lambda total: candidate_monitor_hybrid(
            total, neutral_monitor_curve
        ),
        "candidate_monitor_hybrid_d60_chroma": lambda total: (
            real_frame_ab.apply_d60_monitor_chroma_calibration(
                candidate,
                total,
                candidate_monitor_hybrid(total, neutral_monitor_curve),
                d60_monitor_delta_lut,
            )
        ),
        "candidate_h61_clean": lambda total: candidate.render_2383_projection_from_record_density(
            total[None, None], include_reference_flare=False
        )[0, 0],
        "candidate_old_monitor": candidate_legacy_monitor,
    }

    vendor_names = [
        "resolve_rec709_d55",
        "resolve_rec709_d60",
        "resolve_rec709_d65",
        "adobe_5218_2383",
        "filmvision_sd1",
        "filmvision_sd2",
        "filmvision_sd3",
    ]
    vendor_angles: dict[str, dict[str, float]] = {}
    vendor_magnitudes: dict[str, dict[str, float]] = {}
    for vendor in vendor_names:
        lut = load_cube(SOURCES[vendor])
        fn = lambda value, lut=lut: sample_3d(lut, value)
        center = neutral_for_output(fn, 0.50)
        neutral_encoded = fn(np.full(3, center))
        gamma = 2.2 if vendor.startswith("adobe") else 2.4
        neutral_linear = rec709_decode(neutral_encoded, gamma)
        vendor_angles[vendor] = {}
        vendor_magnitudes[vendor] = {}
        for patch, direction in patch_vectors.items():
            encoded = fn(np.full(3, center) + direction)
            vector = delta_ab(candidate, rec709_decode(encoded, gamma), neutral_linear)
            vendor_angles[vendor][patch] = angle_degrees(vector)
            vendor_magnitudes[vendor][patch] = float(np.linalg.norm(vector))

    consensus_angle = {
        patch: circular_median([vendor_angles[v][patch] for v in vendor_names])
        for patch in patch_vectors
    }
    vendor_spread = {
        patch: float(
            np.median(
                [angular_distance(vendor_angles[v][patch], consensus_angle[patch]) for v in vendor_names]
            )
        )
        for patch in patch_vectors
    }

    rendered: dict[str, object] = {}
    for name, renderer in renderers.items():
        neutral = renderer(neutral_total)
        patch_rows = {}
        errors = []
        for patch, total in totals.items():
            output = renderer(total)
            vector = delta_ab(candidate, output, neutral)
            angle = angle_degrees(vector)
            error = angular_distance(angle, consensus_angle[patch])
            errors.append(error)
            patch_rows[patch] = {
                "rgb_linear": output.tolist(),
                "delta_oklab_ab": vector.tolist(),
                "angle_degrees": angle,
                "consensus_angle_degrees": consensus_angle[patch],
                "angular_error_degrees": error,
            }
        rendered[name] = {
            "neutral_rgb_linear": neutral.tolist(),
            "patches": patch_rows,
            "mean_angular_error_degrees": float(np.mean(errors)),
            "median_angular_error_degrees": float(np.median(errors)),
            "maximum_angular_error_degrees": float(np.max(errors)),
        }

    # Brightness holdout: the fit used only the 18% scene point. Find neutral
    # scene levels that land at four finished-display code values, then compare
    # local coupling against the seven finished Rec.709/sRGB vendor cubes.
    local_document = json.loads(VENDOR_LOCAL_METRICS.read_text())
    vendor_local_names = [
        "resolve_rec709_d55",
        "resolve_rec709_d60",
        "resolve_rec709_d65",
        "adobe_5218_2383",
        "filmvision_sd1",
        "filmvision_sd2",
        "filmvision_sd3",
    ]
    target_codes = [0.18, 0.35, 0.50, 0.70]
    vendor_local_median: dict[str, list[list[float]]] = {}
    for target_code in target_codes:
        matrices = []
        for vendor in vendor_local_names:
            row = min(
                local_document["looks"][vendor],
                key=lambda item: abs(item["target_output_geomean"] - target_code),
            )
            matrices.append(np.array(row["row_normalized_log_jacobian"]))
        vendor_local_median[str(target_code)] = np.median(matrices, axis=0).tolist()

    stops = np.linspace(-9.0, 6.0, 301)
    neutral_samples = []
    for stop in stops:
        level = 0.18 * (2.0**stop)
        scene = np.full((1, 1, 3), level, dtype=np.float32)
        film = candidate.vgamut_to_balanced_film_rgb(
            candidate.bt2020_to_panasonic_vgamut(scene)
        )
        total = candidate.develop_5279_record_density(
            candidate.film_records_from_rgb(film)
        )[0, 0]
        physical = candidate_physical(total)
        display_code = float(
            np.exp(np.mean(np.log(np.maximum(physical, 1e-8)))) ** (1.0 / 2.4)
        )
        neutral_samples.append((stop, display_code, total))

    brightness_holdout: dict[str, object] = {}
    off_diagonal = ~np.eye(3, dtype=bool)
    brightness_renderers = {
        "v21_monitor": renderers["v21_monitor"],
        "candidate_physical": candidate_physical,
        "candidate_old_monitor": renderers["candidate_old_monitor"],
        "candidate_monitor_physical_hue_bounded_sat": candidate_monitor_physical_hue_bounded_sat,
        "candidate_monitor_channel_curve": renderers["candidate_monitor_channel_curve"],
        "candidate_monitor_hybrid": renderers["candidate_monitor_hybrid"],
    }
    for target_code in target_codes:
        stop, actual_code, total = min(
            neutral_samples, key=lambda item: abs(item[1] - target_code)
        )
        target_matrix = np.array(vendor_local_median[str(target_code)])
        rows = {}
        for name, renderer in brightness_renderers.items():
            matrix = local_normalized_log_jacobian(candidate, total, renderer)
            rows[name] = {
                "row_normalized_log_jacobian": matrix.tolist(),
                "off_diagonal_rmse_to_vendor_median": float(
                    np.sqrt(
                        np.mean(
                            np.square(
                                matrix[off_diagonal] - target_matrix[off_diagonal]
                            )
                        )
                    )
                ),
            }
        brightness_holdout[str(target_code)] = {
            "selected_scene_stop_from_18_percent": float(stop),
            "actual_candidate_physical_display_code": actual_code,
            "vendor_median_matrix": target_matrix.tolist(),
            "renderers": rows,
        }

    neutral_scale_rows = []
    for stop in np.linspace(-12.0, 9.0, 85):
        level = 0.18 * (2.0**stop)
        scene = np.full((1, 1, 3), level, dtype=np.float32)
        film = candidate.vgamut_to_balanced_film_rgb(
            candidate.bt2020_to_panasonic_vgamut(scene)
        )
        total = candidate.develop_5279_record_density(
            candidate.film_records_from_rgb(film)
        )[0, 0]
        base_rgb = renderers["v21_monitor"](total)
        hybrid_rgb = renderers["candidate_monitor_hybrid"](total)
        neutral_scale_rows.append(
            {
                "stop": float(stop),
                "v21_rgb": base_rgb.tolist(),
                "candidate_rgb": hybrid_rgb.tolist(),
                "v21_luma": float(np.dot(base_rgb, [0.2126, 0.7152, 0.0722])),
                "candidate_luma": float(
                    np.dot(hybrid_rgb, [0.2126, 0.7152, 0.0722])
                ),
                "candidate_channel_spread": float(
                    np.max(hybrid_rgb) - np.min(hybrid_rgb)
                ),
            }
        )
    neutral_scale = {
        "samples": neutral_scale_rows,
        "maximum_absolute_luma_difference_from_v21": float(
            max(abs(row["candidate_luma"] - row["v21_luma"]) for row in neutral_scale_rows)
        ),
        "candidate_black_floor_at_minus_12_stops": neutral_scale_rows[0][
            "candidate_luma"
        ],
        "candidate_peak_at_plus_9_stops": neutral_scale_rows[-1][
            "candidate_luma"
        ],
        "maximum_candidate_neutral_channel_spread": float(
            max(row["candidate_channel_spread"] for row in neutral_scale_rows)
        ),
        "candidate_luma_monotonic": bool(
            np.all(np.diff([row["candidate_luma"] for row in neutral_scale_rows]) >= -1e-7)
        ),
    }

    metrics = {
        "question": "Does correcting Status-A/analytical-density confusion plus a LAD-anchored 2383 interimage matrix improve finite chromatic directions not used in the fit?",
        "fit_boundary": {
            "fit": "mid-gray row-normalized local log-output Jacobian median only",
            "holdout": "six finite mean-preserving Cineon chromatic directions at +/-0.060",
            "excluded_from_colour_holdout": "BMD ACES LMT, because AP0 linear cannot be compared to finished Rec.709 without adding an ODT",
        },
        "target_local_normalized_jacobian": TARGET_LOCAL_NORMALIZED_JACOBIAN.tolist(),
        "candidate_interimage_matrix": PRINT_INTERIMAGE_MATRIX.tolist(),
        "candidate_interimage_condition_number": float(np.linalg.cond(PRINT_INTERIMAGE_MATRIX)),
        "neutral_monitor_curve": {
            "input_physical_linear": neutral_monitor_curve[0].tolist(),
            "output_display_linear": neutral_monitor_curve[1].tolist(),
        },
        "neutral_cineon_code_rgb": neutral_q.tolist(),
        "patch_vectors": {k: v.tolist() for k, v in patch_vectors.items()},
        "vendor_angles_degrees": vendor_angles,
        "vendor_magnitudes_oklab": vendor_magnitudes,
        "consensus_angles_degrees": consensus_angle,
        "vendor_median_angular_spread_degrees": vendor_spread,
        "renderers": rendered,
        "brightness_holdout": brightness_holdout,
        "neutral_scale": neutral_scale,
    }
    (HERE / "cross_vendor_holdout_metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n"
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
