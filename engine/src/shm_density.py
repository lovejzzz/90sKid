#!/usr/bin/env python3
"""Silver-Halide Morphology (SHM) experimental density formation.

This is an independently generated, Silver-Efex-inspired comparator. It does
not embed or redistribute DxO/Nik stock patches. Confirmed inverse-binomial and
tone-participation mathematics are retained while the former single Gaussian
copula is replaced by a multiscale, non-Gaussian stochastic morphology whose
statistics are bounded by measurements of several installed branded stocks.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from scipy import special

from fsd_density import (
    LOOKUP_LEVELS,
    _lookup_binomial_density,
    _srgb_decode,
    _srgb_encode,
    _transport_luma_without_chroma_modulation,
    binomial_quantile_table,
    tone_taper,
)


# Confirmed Silver Efex luma axis. This intentionally differs from the old
# FSD control's Rec.709 axis; the signal opponent field is held relative to
# this same axis so the density realization cannot manufacture colour speckle.
SHM_LUMA = np.asarray([0.299, 0.587, 0.114], dtype=np.float32)


@dataclass(frozen=True)
class SHMProfile:
    # Refit from a controlled 16-bit, 2048-square Silver Efex Tri-X export.
    # This is a same-class comparator scale, not a 5279 particle count.
    site_count: int = 1250
    # Native-pixel Gaussian scales form a fine/mid/coarse crystal population.
    scales: tuple[float, float, float] = (0.45, 0.90, 1.80)
    weights: tuple[float, float, float] = (0.50, 0.27, 0.23)
    # Weak nonlinear coupling produces clusters and voids without copying a
    # proprietary texture. The coefficient is inside the measured B&W-patch
    # skew/kurtosis envelope, not an asserted 5279 material constant.
    cluster_coupling: float = 0.08
    # A symmetric third Hermite population adds the thick positive tails that
    # distinguish the controlled Tri-X result from a merely correlated
    # Gaussian field.  This was fitted from exported flat fields, not copied
    # from a Nik resource.
    tail_coupling: float = 0.020
    # Tone changes organization, not only amplitude: low density favours the
    # fine population, while high dye/silver density permits larger connected
    # clusters. These are bounded hypotheses, not measured 5279 constants.
    shadow_coarse_bias: float = -0.005
    highlight_coarse_bias: float = 0.005
    population_heterogeneity: float = 0.055
    density_strength: float = 1.0


DEFAULT_PROFILE = SHMProfile()

# Controlled Silver Efex Tri-X 400 black-box export, Grain Intensity 100 and
# Grain Size 1.  Values are the measured ratio between the exported flat-field
# RMS and the N=1250 inverse-binomial candidate after the confirmed taper.  We
# store measurements, not a proprietary texture or stock resource.
_TRIX_TONE = np.asarray(
    [
        0.02499428, 0.08833448, 0.15165942, 0.21499962,
        0.27833982, 0.34166476, 0.40500496, 0.46832990,
        0.53167010, 0.59499504, 0.65833524, 0.72166018,
        0.78500038, 0.84834058, 0.91166552, 0.97500572,
    ],
    dtype=np.float32,
)
_TRIX_GAIN = np.asarray(
    [
        0.304674, 0.282645, 0.361302, 0.546311,
        0.706193, 0.820136, 0.911024, 0.963743,
        1.023304, 1.059569, 1.094774, 1.096378,
        1.057430, 1.011279, 1.245904, 3.179934,
    ],
    dtype=np.float32,
)


def trix_reference_tone_gain(y: np.ndarray) -> np.ndarray:
    """Interpolate the independently measured Tri-X density envelope."""
    return np.interp(
        np.asarray(y, dtype=np.float32), _TRIX_TONE, _TRIX_GAIN,
        left=float(_TRIX_GAIN[0]), right=float(_TRIX_GAIN[-1]),
    ).astype(np.float32)


def _standardize(field: np.ndarray) -> np.ndarray:
    field = field.astype(np.float32, copy=False)
    field -= np.float32(field.mean(dtype=np.float64))
    field /= np.float32(max(field.std(dtype=np.float64), 1.0e-8))
    return field


def morphology_latent_field(
    height: int,
    width: int,
    frame_index: int,
    profile: SHMProfile = DEFAULT_PROFILE,
    tone: np.ndarray | float | None = None,
) -> np.ndarray:
    """Generate a fresh, aperiodic, density-dependent organization field."""
    seed = np.uint64(
        (0x53484D5F35323739 ^ (int(frame_index) * 0x9E3779B97F4A7C15))
        & 0xFFFFFFFFFFFFFFFF
    )
    rng = np.random.Generator(np.random.PCG64DXSM(seed))
    components: list[np.ndarray] = []
    # Independent population fields prevent all scales from sharing one phase.
    for sigma, weight in zip(profile.scales, profile.weights):
        white = rng.standard_normal((height, width), dtype=np.float32)
        if sigma > 0:
            white = cv2.GaussianBlur(
                white,
                (0, 0),
                sigmaX=float(sigma),
                sigmaY=float(sigma),
                borderType=cv2.BORDER_REFLECT_101,
            )
        components.append(_standardize(white))
    if tone is None:
        tone_field = np.full((height, width), 0.5, dtype=np.float32)
    else:
        tone_field = np.broadcast_to(
            np.asarray(tone, dtype=np.float32), (height, width)
        )
    # Smooth shadow/highlight selectors avoid a spectral discontinuity at a
    # tone boundary. Per-pixel RMS normalization preserves the uniform-marginal
    # contract even while the fine/coarse population balance changes.
    shadow = np.clip((0.55 - tone_field) / 0.50, 0.0, 1.0)
    highlight = np.clip((tone_field - 0.45) / 0.50, 0.0, 1.0)
    shadow = shadow * shadow * (3.0 - 2.0 * shadow)
    highlight = highlight * highlight * (3.0 - 2.0 * highlight)
    fine = np.float32(profile.weights[0]) - (
        np.float32(profile.shadow_coarse_bias) * shadow
        + np.float32(profile.highlight_coarse_bias) * highlight
    )
    mid = np.full((height, width), profile.weights[1], dtype=np.float32)
    coarse = np.float32(profile.weights[2]) + (
        np.float32(profile.shadow_coarse_bias) * shadow
        + np.float32(profile.highlight_coarse_bias) * highlight
    )
    # A slowly varying occupancy field changes *population balance* rather
    # than image brightness. Adjacent areas therefore have subtly different
    # power spectra, analogous to a non-uniform crystal population, while the
    # per-pixel RMS normalization below prevents an overlay-like density cloud.
    occupancy = rng.standard_normal((height, width), dtype=np.float32)
    occupancy = cv2.GaussianBlur(
        occupancy, (0, 0), sigmaX=7.5, sigmaY=7.5,
        borderType=cv2.BORDER_REFLECT_101,
    )
    occupancy = _standardize(occupancy)
    population_shift = np.float32(profile.population_heterogeneity) * np.tanh(
        occupancy
    )
    fine = np.maximum(fine - population_shift, 0.02)
    coarse = np.maximum(coarse + population_shift, 0.02)
    norm = np.sqrt(fine * fine + mid * mid + coarse * coarse)
    latent = (
        fine * components[0] + mid * components[1] + coarse * components[2]
    ) / np.maximum(norm, 1.0e-6)
    # Hermite terms retain controllable non-Gaussian cluster/void organization.
    coupling = np.float32(profile.cluster_coupling) * (
        np.float32(0.2625)
        + np.float32(0.25) * np.tanh(occupancy)
        + np.float32(0.45) * (tone_field - np.float32(0.5))
    )
    latent = latent + coupling * (latent * latent - np.float32(1.0))
    tail = np.float32(profile.tail_coupling)
    latent = latent + tail * (latent * latent * latent - np.float32(3.0) * latent)
    # The subsequent measured-RMS envelope owns amplitude. Re-standardizing
    # here keeps skew/kurtosis organization from becoming a hidden gain knob.
    return _standardize(latent)


def morphology_uniform_field(
    height: int,
    width: int,
    frame_index: int,
    profile: SHMProfile = DEFAULT_PROFILE,
    tone: np.ndarray | float | None = None,
) -> np.ndarray:
    field = morphology_latent_field(height, width, frame_index, profile, tone)
    special.ndtr(field, out=field)
    np.clip(
        field,
        0.5 / LOOKUP_LEVELS,
        1.0 - 0.5 / LOOKUP_LEVELS,
        out=field,
    )
    return field


def apply_shm(
    deterministic_linear_rgb: np.ndarray,
    frame_index: int,
    profile: SHMProfile = DEFAULT_PROFILE,
) -> tuple[np.ndarray, dict[str, object]]:
    """Reconstruct display luma through heterogeneous finite-site density."""
    rgb = np.asarray(deterministic_linear_rgb, dtype=np.float32)
    encoded = _srgb_encode(np.clip(rgb, 0.0, 1.0))
    luma = np.einsum(
        "...c,c->...", encoded, SHM_LUMA, optimize=True
    ).astype(np.float32)
    uniform = morphology_uniform_field(
        rgb.shape[0], rgb.shape[1], frame_index, profile, luma
    )
    table = binomial_quantile_table(profile.site_count)
    formed = np.empty_like(luma)
    for y0 in range(0, rgb.shape[0], 128):
        y1 = min(y0 + 128, rgb.shape[0])
        p = luma[y0:y1]
        candidate = _lookup_binomial_density(p, uniform[y0:y1], table)
        alpha = (
            np.float32(profile.density_strength)
            * tone_taper(p)
            * trix_reference_tone_gain(p)
        )
        formed[y0:y1] = p + alpha * (candidate - p)
    np.clip(formed, 0.0, 1.0, out=formed)
    encoded_result, constrained = _transport_luma_without_chroma_modulation(
        encoded, luma, formed
    )
    result = _srgb_decode(encoded_result)
    residual = formed - luma
    stats = {
        "pipeline": "Silver-Halide Morphology (SHM)",
        "status": "independent morphology comparator; not DxO code and not measured 5279",
        "site_count": profile.site_count,
        "scales_native_px": list(profile.scales),
        "weights": list(profile.weights),
        "cluster_coupling": profile.cluster_coupling,
        "tail_coupling": profile.tail_coupling,
        "shadow_coarse_bias": profile.shadow_coarse_bias,
        "highlight_coarse_bias": profile.highlight_coarse_bias,
        "population_heterogeneity": profile.population_heterogeneity,
        "density_strength": profile.density_strength,
        "luma_axis": "Rec.601 / confirmed Silver Efex 0.299, 0.587, 0.114",
        "tone_envelope": (
            "controlled Silver Efex Tri-X 400 16-bit flat-field RMS fit; "
            "Intensity 100, Grain Size 1, 2048-square source"
        ),
        "gamut_luma_constraint_fraction": float(constrained),
        "code_luma_delta_mean": float(residual.mean(dtype=np.float64)),
        "code_luma_delta_rms": float(np.sqrt(np.mean(residual * residual, dtype=np.float64))),
    }
    return result, stats
