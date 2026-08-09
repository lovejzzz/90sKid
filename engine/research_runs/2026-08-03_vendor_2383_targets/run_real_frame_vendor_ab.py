#!/usr/bin/env python3
"""Real-frame A/B against Resolve's independently supplied 2383 views.

This is deliberately a display-colour validation, not a claim that Resolve's
LUTs expose Kodak's internal chemistry.  D55/D60/D65 form an independent
white-point bracket.  V21 and the analytical/interimage candidate receive the
same deterministic 5279 record-density image and are compared in linear-light
OKLab after decoding each vendor LUT's documented gamma-2.4 output.
"""

from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from analyze_vendor_luts import SOURCES, load_cube


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src" / "emulsion_experiment.py"
HOLDOUT = HERE / "run_cross_vendor_holdout.py"
RAW = Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV")
DECODER = Path("/tmp/prores_raw_float_decode")
OUTPUT = HERE / "real_frame12_vendor_ab"
FRAME = 12
SOURCE_WIDTH = 5760
SOURCE_HEIGHT = 4320
WORK_WIDTH = 1440
WORK_HEIGHT = 1080
EXPOSURE_STOPS = 0.45


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_frame() -> np.ndarray:
    expected = SOURCE_WIDTH * SOURCE_HEIGHT * 3 * 4
    result = subprocess.run(
        [str(DECODER), str(RAW), str(FRAME), "1"],
        check=True,
        capture_output=True,
    )
    if len(result.stdout) != expected:
        raise RuntimeError(
            f"decoder returned {len(result.stdout)} bytes; expected {expected}"
        )
    native = np.frombuffer(result.stdout, dtype="<f4").reshape(
        SOURCE_HEIGHT, SOURCE_WIDTH, 3
    )
    reduced = cv2.resize(
        native, (WORK_WIDTH, WORK_HEIGHT), interpolation=cv2.INTER_AREA
    ).astype(np.float32)
    del native, result
    gc.collect()
    return reduced


def sample_cube_image(lut: np.ndarray, image: np.ndarray, rows: int = 96) -> np.ndarray:
    """Trilinear .cube sampling; load_cube stores axes as [blue, green, red]."""
    source = np.clip(np.asarray(image, dtype=np.float32), 0.0, 1.0)
    output = np.empty_like(source)
    limit = lut.shape[0] - 1
    for row0 in range(0, source.shape[0], rows):
        row1 = min(row0 + rows, source.shape[0])
        stripe = source[row0:row1]
        position = stripe * limit
        lower = np.floor(position).astype(np.int16)
        upper = np.minimum(lower + 1, limit)
        fraction = position - lower
        r0, g0, b0 = (lower[..., index] for index in range(3))
        r1, g1, b1 = (upper[..., index] for index in range(3))
        fr, fg, fb = (fraction[..., index, None] for index in range(3))
        c000 = lut[b0, g0, r0]
        c100 = lut[b0, g0, r1]
        c010 = lut[b0, g1, r0]
        c110 = lut[b0, g1, r1]
        c001 = lut[b1, g0, r0]
        c101 = lut[b1, g0, r1]
        c011 = lut[b1, g1, r0]
        c111 = lut[b1, g1, r1]
        c00 = c000 * (1.0 - fr) + c100 * fr
        c10 = c010 * (1.0 - fr) + c110 * fr
        c01 = c001 * (1.0 - fr) + c101 * fr
        c11 = c011 * (1.0 - fr) + c111 * fr
        output[row0:row1] = (
            (c00 * (1.0 - fg) + c10 * fg) * (1.0 - fb)
            + (c01 * (1.0 - fg) + c11 * fg) * fb
        )
    return output


def continuous_cineon_image(e, total_density: np.ndarray) -> np.ndarray:
    scanner = e.scanner_density_from_total_record_density(total_density)
    gain = 0.700 / e.NEUTRAL_MID_SCANNER_DENSITY
    return ((95.0 + scanner * gain / 0.002) / 1023.0).astype(np.float32)


def gamma24_decode(encoded: np.ndarray) -> np.ndarray:
    return np.power(np.clip(encoded, 0.0, 1.0), 2.4).astype(np.float32)


def render_candidate_threshold(
    e, total_density: np.ndarray, transition_high: float, rows: int = 96
) -> np.ndarray:
    """Candidate monitor view with a held-out finite-colour transition width."""
    result = np.empty_like(total_density, dtype=np.float32)
    for row0 in range(0, total_density.shape[0], rows):
        row1 = min(row0 + rows, total_density.shape[0])
        stripe = total_density[row0:row1]
        physical = e.apply_2383_monitor_neutral_curve(
            e._render_2383_projection_uncalibrated(stripe)
        )
        calibrated = e.match_2383_projection_to_rec709_monitor(
            e.render_2383_projection_from_record_density(
                stripe, include_reference_flare=True
            ),
            e.finish_cineon_scan_for_bluray(
                e.render_cineon_scan_master_from_record_density(stripe)
            ),
        )
        maximum = np.max(physical, axis=-1)
        relative_chroma = (maximum - np.min(physical, axis=-1)) / np.maximum(
            maximum, 1e-6
        )
        weight = e.smoothstep(0.02, transition_high, relative_chroma)
        physical_lab = e.linear_rec709_to_oklab(physical)
        calibrated_lab = e.linear_rec709_to_oklab(calibrated)
        hybrid = e.compress_oklab_chroma_to_rec709(
            e.oklab_to_linear_rec709(
                physical_lab * (1.0 - weight[..., None])
                + calibrated_lab * weight[..., None]
            )
        )
        scan = e.finish_cineon_scan_for_bluray(
            e.render_cineon_scan_master_from_record_density(stripe)
        )
        scan_max = np.max(scan, axis=-1)
        scan_chroma = (scan_max - np.min(scan, axis=-1)) / np.maximum(
            scan_max, 1e-6
        )
        scan_luma = np.einsum(
            "...c,c->...", np.maximum(scan, 0.0), [0.2126, 0.7152, 0.0722]
        )
        neutral = np.interp(
            scan_luma,
            e.PRINT_MONITOR_SCAN_LUMA_ANCHORS,
            e.PRINT_MONITOR_TARGET_LUMA_ANCHORS,
        ).astype(np.float32)
        highlight_weight = e.smoothstep(0.82, 0.94, neutral) * (
            1.0 - e.smoothstep(0.010, 0.060, scan_chroma)
        )
        result[row0:row1] = (
            hybrid * (1.0 - highlight_weight[..., None])
            + neutral[..., None] * highlight_weight[..., None]
        )
    return np.clip(result, 0.0, 1.0)


def reset_print_caches(e) -> None:
    e._PRINT_2383_NEUTRAL_SHAPERS = None
    e._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    e._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    e._PRINT_2383_MONITOR_DELTA_LUT = None
    e._PRINT_2383_MONITOR_NEUTRAL_CURVE = None


def render_interimage_strength_sweep(
    e, total_density: np.ndarray, original_matrix: np.ndarray
) -> dict[str, np.ndarray]:
    """Hold out fractions of the fitted matrix to detect double coupling."""
    outputs: dict[str, np.ndarray] = {}
    identity = np.eye(3, dtype=np.float32)
    for strength in (0.0, 0.25, 0.50, 0.75):
        e.PRINT_2383_INTERIMAGE_MATRIX = (
            identity * (1.0 - strength) + original_matrix * strength
        ).astype(np.float32)
        reset_print_caches(e)
        outputs[f"v22_interimage_{strength:.02f}"] = (
            e.render_2383_monitor_projection_from_record_density(total_density)
        )
    e.PRINT_2383_INTERIMAGE_MATRIX = original_matrix.copy()
    reset_print_caches(e)
    return outputs


def sample_density_lut(e, lut: np.ndarray, total_density: np.ndarray) -> np.ndarray:
    net_min = -0.16
    net_max = e.NEGATIVE_5279_MAX_RECORD_DENSITY
    source = np.asarray(total_density, dtype=np.float32)
    position = np.clip(
        (source - e.SENSITO_DMIN_RGB - net_min)
        * ((lut.shape[0] - 1) / (net_max - net_min)),
        0.0,
        lut.shape[0] - 1.00001,
    )
    lower = np.floor(position).astype(np.int16)
    upper = np.minimum(lower + 1, lut.shape[0] - 1)
    fraction = position - lower
    r0, g0, b0 = (lower[..., index] for index in range(3))
    r1, g1, b1 = (upper[..., index] for index in range(3))
    fr, fg, fb = (fraction[..., index, None] for index in range(3))
    c000 = lut[r0, g0, b0]
    c100 = lut[r1, g0, b0]
    c010 = lut[r0, g1, b0]
    c110 = lut[r1, g1, b0]
    c001 = lut[r0, g0, b1]
    c101 = lut[r1, g0, b1]
    c011 = lut[r0, g1, b1]
    c111 = lut[r1, g1, b1]
    c00 = c000 * (1.0 - fr) + c100 * fr
    c10 = c010 * (1.0 - fr) + c110 * fr
    c01 = c001 * (1.0 - fr) + c101 * fr
    c11 = c011 * (1.0 - fr) + c111 * fr
    return (
        (c00 * (1.0 - fg) + c10 * fg) * (1.0 - fb)
        + (c01 * (1.0 - fg) + c11 * fg) * fb
    ).astype(np.float32)


def build_d60_monitor_chroma_delta_lut(e, size: int = 25) -> np.ndarray:
    """Fit only monitor chroma to Resolve D60; retain physical lightness."""
    net_min = -0.16
    net_max = e.NEGATIVE_5279_MAX_RECORD_DENSITY
    axis = np.linspace(net_min, net_max, size, dtype=np.float32)
    red, green, blue = np.meshgrid(axis, axis, axis, indexing="ij")
    total = np.stack([red, green, blue], axis=-1) + e.SENSITO_DMIN_RGB
    base_renderer = getattr(
        e,
        "_render_2383_monitor_projection_base_from_record_density",
        e.render_2383_monitor_projection_from_record_density,
    )
    candidate = base_renderer(total)
    cineon = continuous_cineon_image(e, total)
    d60_cube = load_cube(SOURCES["resolve_rec709_d60"])
    d60 = gamma24_decode(sample_cube_image(d60_cube, cineon))
    neutral_cineon_value = np.mean(cineon, axis=-1, keepdims=True)
    neutral_cineon = np.repeat(neutral_cineon_value, 3, axis=-1)
    d60_neutral = gamma24_decode(sample_cube_image(d60_cube, neutral_cineon))
    candidate_lab = e.linear_rec709_to_oklab(candidate)
    d60_lab = e.linear_rec709_to_oklab(d60)
    d60_neutral_lab = e.linear_rec709_to_oklab(d60_neutral)
    candidate_chroma = np.linalg.norm(candidate_lab[..., 1:3], axis=-1)
    d60_relative_ab = d60_lab[..., 1:3] - d60_neutral_lab[..., 1:3]
    d60_chroma = np.linalg.norm(d60_relative_ab, axis=-1)
    d60_direction = d60_relative_ab / np.maximum(
        d60_chroma[..., None], 1e-6
    )
    # Use D60's absolute opponent excursion after removing its neutral white,
    # not its C/L ratio. Our physical-print monitor curve is deliberately more
    # open than Resolve's gamma-2.4 proof; multiplying D60 saturation by our
    # higher lightness would recreate the old over-rich blue/green/yellow.
    # One-percent interpolation headroom prevents a 25^3 lattice corner from
    # numerically overshooting the source transform's finite-colour envelope.
    target_ab = d60_direction * (0.99 * d60_chroma)[..., None]
    cineon_chroma = np.max(cineon, axis=-1) - np.min(cineon, axis=-1)
    # Input-code chroma is the stable neutral discriminator. D60's display
    # white is intentionally not D65, so output chroma alone would tint the
    # neutral axis and would overwrite microscopic interimage grain colour.
    colour_weight = e.smoothstep(0.008, 0.040, cineon_chroma)
    target_lab = candidate_lab.copy()
    target_lab[..., 1:3] = (
        candidate_lab[..., 1:3] * (1.0 - colour_weight[..., None])
        + target_ab * colour_weight[..., None]
    )
    return (target_lab - candidate_lab).astype(np.float32)


def polynomial_13_features(cineon: np.ndarray) -> np.ndarray:
    value = np.asarray(cineon, dtype=np.float64) - 0.5
    red, green, blue = (value[..., index] for index in range(3))
    return np.stack(
        [
            np.ones_like(red),
            red,
            green,
            blue,
            red * red,
            green * green,
            blue * blue,
            red * red * red,
            green * green * green,
            blue * blue * blue,
            red * green,
            red * blue,
            green * blue,
        ],
        axis=-1,
    )


def fit_d60_13term_polynomial(e, delta_lut: np.ndarray) -> np.ndarray:
    size = delta_lut.shape[0]
    axis = np.linspace(-0.16, e.NEGATIVE_5279_MAX_RECORD_DENSITY, size)
    red, green, blue = np.meshgrid(axis, axis, axis, indexing="ij")
    total = np.stack([red, green, blue], axis=-1) + e.SENSITO_DMIN_RGB
    cineon = continuous_cineon_image(e, total)
    features = polynomial_13_features(cineon).reshape(-1, 13)
    target = delta_lut[..., 1:3].reshape(-1, 2).astype(np.float64)
    # Tiny ridge term improves extrapolation at cube corners without altering
    # any perceptible fitted colour in the useful density volume.
    ridge = 1e-6
    augmented_x = np.concatenate(
        [features, np.sqrt(ridge) * np.eye(13)], axis=0
    )
    augmented_y = np.concatenate([target, np.zeros((13, 2))], axis=0)
    coefficients, *_ = np.linalg.lstsq(augmented_x, augmented_y, rcond=None)
    return coefficients.astype(np.float32)


def apply_d60_monitor_chroma_calibration(
    e, total_density: np.ndarray, candidate: np.ndarray, lut: np.ndarray
) -> np.ndarray:
    lab = e.linear_rec709_to_oklab(candidate)
    delta = sample_density_lut(e, lut, total_density)
    cineon = continuous_cineon_image(e, total_density)
    cineon_chroma = np.max(cineon, axis=-1) - np.min(cineon, axis=-1)
    neutral_guard = e.smoothstep(0.008, 0.040, cineon_chroma)
    lab += delta * neutral_guard[..., None]
    return np.clip(
        e.compress_oklab_chroma_to_rec709(e.oklab_to_linear_rec709(lab)),
        0.0,
        1.0,
    )


def apply_d60_polynomial_calibration(
    e, total_density: np.ndarray, candidate: np.ndarray, coefficients: np.ndarray
) -> np.ndarray:
    cineon = continuous_cineon_image(e, total_density)
    chroma = np.max(cineon, axis=-1) - np.min(cineon, axis=-1)
    guard = e.smoothstep(0.008, 0.040, chroma)
    delta_ab = np.einsum(
        "...f,fc->...c", polynomial_13_features(cineon), coefficients
    ).astype(np.float32)
    lab = e.linear_rec709_to_oklab(candidate)
    lab[..., 1:3] += delta_ab * guard[..., None]
    return np.clip(
        e.compress_oklab_chroma_to_rec709(e.oklab_to_linear_rec709(lab)),
        0.0,
        1.0,
    )


def save_linear_srgb(e, path: Path, linear: np.ndarray) -> None:
    encoded = e.srgb_encode(np.clip(linear, 0.0, 1.0))
    image = np.rint(encoded * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 96])


def hue_distance_degrees(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.abs((a - b + 180.0) % 360.0 - 180.0)


def percentile_rows(values: np.ndarray) -> dict[str, float]:
    return {
        "median": float(np.median(values)),
        "p75": float(np.percentile(values, 75)),
        "p90": float(np.percentile(values, 90)),
        "p95": float(np.percentile(values, 95)),
    }


def compare_to_vendor(e, rendered: np.ndarray, vendor: np.ndarray) -> dict[str, object]:
    rendered_lab = e.linear_rec709_to_oklab(np.maximum(rendered, 0.0))
    vendor_lab = e.linear_rec709_to_oklab(np.maximum(vendor, 0.0))
    delta = np.linalg.norm(rendered_lab - vendor_lab, axis=-1)
    rendered_chroma = np.linalg.norm(rendered_lab[..., 1:3], axis=-1)
    vendor_chroma = np.linalg.norm(vendor_lab[..., 1:3], axis=-1)
    rendered_hue = np.degrees(np.arctan2(rendered_lab[..., 2], rendered_lab[..., 1]))
    vendor_hue = np.degrees(np.arctan2(vendor_lab[..., 2], vendor_lab[..., 1]))
    valid = (
        (vendor_chroma > 0.025)
        & (rendered_chroma > 0.015)
        & (vendor_lab[..., 0] > 0.08)
        & (vendor_lab[..., 0] < 0.92)
    )
    hue_error = hue_distance_degrees(rendered_hue[valid], vendor_hue[valid])
    # Foliage dominates this frame.  This mask is defined only by the held-out
    # vendor image so V21 and the candidate receive identical pixels.
    foliage = valid & (vendor_hue > 95.0) & (vendor_hue < 155.0)
    foliage_error = hue_distance_degrees(
        rendered_hue[foliage], vendor_hue[foliage]
    )
    sector_rows: dict[str, object] = {}
    sectors = {
        "red": (-45.0, 45.0),
        "yellow": (45.0, 95.0),
        "green": (95.0, 155.0),
        "cyan": (155.0, 205.0),
        "blue": (-155.0, -95.0),
        "magenta": (-95.0, -45.0),
    }
    for name, (low, high) in sectors.items():
        if high > 180.0:
            sector = valid & ((vendor_hue >= low) | (vendor_hue < high - 360.0))
        else:
            sector = valid & (vendor_hue >= low) & (vendor_hue < high)
        count = int(np.count_nonzero(sector))
        if count:
            errors = hue_distance_degrees(rendered_hue[sector], vendor_hue[sector])
            sector_rows[name] = {
                "pixel_fraction": float(np.mean(sector)),
                "median_hue_error_degrees": float(np.median(errors)),
                "p90_hue_error_degrees": float(np.percentile(errors, 90)),
            }
    return {
        "oklab_delta": percentile_rows(delta),
        "chromatic_pixel_fraction": float(np.mean(valid)),
        "hue_error_degrees": percentile_rows(hue_error),
        "foliage_pixel_fraction": float(np.mean(foliage)),
        "foliage_hue_error_degrees": percentile_rows(foliage_error),
        "foliage_median_hue_degrees": {
            "render": float(np.median(rendered_hue[foliage])),
            "vendor": float(np.median(vendor_hue[foliage])),
        },
        "foliage_median_chroma": {
            "render": float(np.median(rendered_chroma[foliage])),
            "vendor": float(np.median(vendor_chroma[foliage])),
        },
        "hue_sectors": sector_rows,
    }


def bracket_membership(e, rendered: np.ndarray, vendors: dict[str, np.ndarray]) -> dict[str, object]:
    render_lab = e.linear_rec709_to_oklab(np.maximum(rendered, 0.0))
    vendor_labs = {
        name: e.linear_rec709_to_oklab(np.maximum(image, 0.0))
        for name, image in vendors.items()
    }
    vendor_hues = np.stack(
        [np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) for lab in vendor_labs.values()]
    )
    vendor_chromas = np.stack(
        [np.linalg.norm(lab[..., 1:3], axis=-1) for lab in vendor_labs.values()]
    )
    render_hue = np.degrees(np.arctan2(render_lab[..., 2], render_lab[..., 1]))
    render_chroma = np.linalg.norm(render_lab[..., 1:3], axis=-1)
    center_hue = np.degrees(
        np.arctan2(
            np.mean(np.sin(np.radians(vendor_hues)), axis=0),
            np.mean(np.cos(np.radians(vendor_hues)), axis=0),
        )
    )
    vendor_radius = np.max(hue_distance_degrees(vendor_hues, center_hue[None]), axis=0)
    render_distance = hue_distance_degrees(render_hue, center_hue)
    valid = (
        (np.min(vendor_chromas, axis=0) > 0.025)
        & (render_chroma > 0.015)
        & (vendor_radius < 35.0)
    )
    inside_hue = render_distance <= vendor_radius + 2.0
    chroma_min = np.min(vendor_chromas, axis=0)
    chroma_max = np.max(vendor_chromas, axis=0)
    inside_chroma = (render_chroma >= 0.85 * chroma_min) & (render_chroma <= 1.15 * chroma_max)
    return {
        "eligible_pixel_fraction": float(np.mean(valid)),
        "hue_inside_d55_d60_d65_plus_2deg_fraction": float(np.mean(inside_hue[valid])),
        "chroma_inside_relaxed_vendor_range_fraction": float(np.mean(inside_chroma[valid])),
        "joint_inside_fraction": float(np.mean((inside_hue & inside_chroma)[valid])),
        "distance_outside_hue_bracket_degrees": percentile_rows(
            np.maximum(render_distance[valid] - vendor_radius[valid], 0.0)
        ),
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    emulsion = load_module("emulsion_real_frame_candidate", SRC)
    holdout = load_module("emulsion_real_frame_holdout", HOLDOUT)
    holdout.install_v21_baseline()

    raw = decode_frame()
    film = emulsion.scene_to_5279_film_rgb(
        raw,
        exposure_stops=EXPOSURE_STOPS,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    del raw
    density = emulsion.develop_5279_record_density(
        emulsion.film_records_from_rgb(film)
    )
    del film
    gc.collect()

    cineon = continuous_cineon_image(emulsion, density)
    v21 = holdout.baseline.render_2383_monitor_projection_from_record_density(density)
    base_renderer = getattr(
        emulsion,
        "_render_2383_monitor_projection_base_from_record_density",
        emulsion.render_2383_monitor_projection_from_record_density,
    )
    v22 = base_renderer(density)
    threshold_variants = {
        f"v22_transition_{high:.02f}": render_candidate_threshold(
            emulsion, density, high
        )
        for high in (0.04, 0.05, 0.07, 0.09)
    }
    interimage_variants = render_interimage_strength_sweep(
        emulsion, density, emulsion.PRINT_2383_INTERIMAGE_MATRIX.copy()
    )
    d60_chroma_lut = build_d60_monitor_chroma_delta_lut(emulsion)
    d60_calibrated = apply_d60_monitor_chroma_calibration(
        emulsion, density, v22, d60_chroma_lut
    )
    d60_polynomial_coefficients = fit_d60_13term_polynomial(
        emulsion, d60_chroma_lut
    )
    d60_polynomial = apply_d60_polynomial_calibration(
        emulsion, density, v22, d60_polynomial_coefficients
    )
    vendors: dict[str, np.ndarray] = {}
    for short, key in (("d55", "resolve_rec709_d55"), ("d60", "resolve_rec709_d60"), ("d65", "resolve_rec709_d65")):
        encoded = sample_cube_image(load_cube(SOURCES[key]), cineon)
        vendors[short] = gamma24_decode(encoded)
        save_linear_srgb(emulsion, OUTPUT / f"resolve_2383_{short}.jpg", vendors[short])

    save_linear_srgb(emulsion, OUTPUT / "v21_deterministic.jpg", v21)
    save_linear_srgb(emulsion, OUTPUT / "v22_candidate_deterministic.jpg", v22)
    for name, image in threshold_variants.items():
        save_linear_srgb(emulsion, OUTPUT / f"{name}.jpg", image)
    for name, image in interimage_variants.items():
        save_linear_srgb(emulsion, OUTPUT / f"{name}.jpg", image)
    save_linear_srgb(
        emulsion, OUTPUT / "v22_d60_chroma_calibrated.jpg", d60_calibrated
    )
    save_linear_srgb(
        emulsion, OUTPUT / "v22_d60_13term_polynomial.jpg", d60_polynomial
    )
    np.savez_compressed(
        OUTPUT / "research_d60_monitor_chroma_delta_lut_25.npz",
        delta_oklab=d60_chroma_lut,
        net_density_min=np.float32(-0.16),
        net_density_max=np.float32(emulsion.NEGATIVE_5279_MAX_RECORD_DENSITY),
    )
    (OUTPUT / "research_d60_13term_polynomial.json").write_text(
        json.dumps(
            {
                "feature_order": [
                    "1", "r", "g", "b", "r2", "g2", "b2",
                    "r3", "g3", "b3", "rg", "rb", "gb",
                ],
                "input_center": 0.5,
                "output": "delta Oklab a,b only",
                "coefficients_13x2": d60_polynomial_coefficients.tolist(),
            },
            indent=2,
        )
        + "\n"
    )
    save_linear_srgb(
        emulsion,
        OUTPUT / "cineon_input_falsecolour.jpg",
        np.clip(cineon, 0.0, 1.0),
    )

    result: dict[str, object] = {
        "scope": "real RAW frame, reduced in extended-linear light before deterministic 5279 processing; vendor LUTs are independent display-colour brackets, not chemical ground truth",
        "raw": str(RAW),
        "raw_sha256": sha256(RAW),
        "frame": FRAME,
        "native_dimensions": [SOURCE_WIDTH, SOURCE_HEIGHT],
        "analysis_dimensions": [WORK_WIDTH, WORK_HEIGHT],
        "exposure_stops": EXPOSURE_STOPS,
        "source_hashes": {
            "production_model": sha256(SRC),
            "v21_reconstruction_test": sha256(HOLDOUT),
            **{name: sha256(SOURCES[f"resolve_rec709_{name}"]) for name in ("d55", "d60", "d65")},
        },
        "comparisons": {},
        "whitepoint_bracket": {},
    }
    models = {
        "v21": v21,
        "v22_candidate": v22,
        **threshold_variants,
        **interimage_variants,
        "v22_d60_chroma_calibrated": d60_calibrated,
        "v22_d60_13term_polynomial": d60_polynomial,
    }
    for model_name, rendered in models.items():
        result["comparisons"][model_name] = {
            name: compare_to_vendor(emulsion, rendered, vendor)
            for name, vendor in vendors.items()
        }
        result["whitepoint_bracket"][model_name] = bracket_membership(
            emulsion, rendered, vendors
        )

    (OUTPUT / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
