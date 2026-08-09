#!/usr/bin/env python3
"""Finite-Site Density (FSD) comparator.

FSD is an independent, Silver-Efex-inspired control pipeline.  It uses the
confirmed finite-binomial density lookup and tone-dependent replacement law,
but it does not claim any Nik branded-film texture or any 5279 chemistry.
Colour is held to the deterministic observer's opponent field so the
experiment isolates density formation rather than creative grading.
"""

from __future__ import annotations

from functools import lru_cache

import cv2
import numpy as np
from scipy import special, stats


LUMA = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
LOOKUP_LEVELS = 512


def tone_taper(y: np.ndarray) -> np.ndarray:
    """Confirmed Silver Efex piecewise density-participation taper."""
    y = np.asarray(y, dtype=np.float32)
    low = (
        (((1811.956543 * y - 876.202087) * y + 117.616173) * y + 0.764699578)
        * y
        + 0.25
    )
    high = (
        (((1811.956543 * y - 6371.624023) * y + 8360.749023) * y - 4855.216797)
        * y
        + 1054.385376
    )
    return np.clip(
        np.where(y < 0.2, low, np.where(y > 0.8, high, 1.0)),
        0.0,
        1.0,
    ).astype(np.float32)


def uniform_hash_field(height: int, width: int, frame_index: int) -> np.ndarray:
    """Extend the confirmed ARM64 uint32 lookup hash over film coordinates.

    The installed engine materializes a 256 x 256 table.  For motion, FSD
    evaluates the same integer hash over adjacent, non-overlapping frame
    coordinates instead of visibly tiling the small table or animating a
    display-space noise plate.
    """
    result = np.empty((height, width), dtype=np.float32)
    x_term = np.arange(width, dtype=np.uint32) * np.uint32(1025)
    frame_y = np.uint64(frame_index) * np.uint64(height)
    for y0 in range(0, height, 128):
        y1 = min(y0 + 128, height)
        rows64 = frame_y + np.arange(y0, y1, dtype=np.uint64)
        state = (rows64 & np.uint64(0xFFFFFFFF)).astype(np.uint32)
        state *= np.uint32(1025)
        state ^= state >> np.uint32(6)
        state *= np.uint32(1025)
        state = state[:, None] + x_term[None, :]
        hashed = state ^ (state >> np.uint32(6))
        hashed *= np.uint32(9)
        hashed ^= hashed >> np.uint32(11)
        hashed *= np.uint32(32769)
        result[y0:y1] = (
            (hashed & np.uint32(0xFFFF)).astype(np.float64) / 65535.0
        ).astype(np.float32)
    return result


def correlated_uniform_field(
    height: int,
    width: int,
    frame_index: int,
    correlation_sigma: float,
) -> np.ndarray:
    """Create an isotropic Gaussian-copula field with a uniform marginal.

    The recovered 256-square engine lookup establishes the uniform variate
    contract, but extending its coordinate hash beyond that table introduces
    a measurable x/y correlation imbalance.  FSD therefore uses a seeded
    modern generator for the moving field and retains ``uniform_hash_field``
    only as the exact executable reconstruction of the installed lookup.
    """
    seed = np.uint64(
        (0x4653445F35323739 ^ (int(frame_index) * 0x9E3779B97F4A7C15))
        & 0xFFFFFFFFFFFFFFFF
    )
    generator = np.random.Generator(np.random.PCG64DXSM(seed))
    field = generator.random((height, width), dtype=np.float32)
    np.clip(field, 0.5 / 2**32, 1.0 - 0.5 / 2**32, out=field)
    special.ndtri(field, out=field)
    if correlation_sigma > 0.0:
        blurred = cv2.GaussianBlur(
            field,
            (0, 0),
            sigmaX=float(correlation_sigma),
            sigmaY=float(correlation_sigma),
            borderType=cv2.BORDER_REFLECT_101,
        )
        field = blurred.astype(np.float32, copy=False)
    field -= np.float32(field.mean(dtype=np.float64))
    field /= np.float32(max(field.std(dtype=np.float64), 1.0e-8))
    special.ndtr(field, out=field)
    # A finite inverse CDF is defined for u in the open interval (0, 1).
    # The engine's uint32 LCG uses state * 2^-32 and therefore never reaches
    # one; retain the same endpoint contract after float32 copula conversion.
    np.clip(
        field,
        0.5 / LOOKUP_LEVELS,
        1.0 - 0.5 / LOOKUP_LEVELS,
        out=field,
    )
    return field


@lru_cache(maxsize=8)
def binomial_quantile_table(site_count: int) -> np.ndarray:
    """Build the confirmed 512 x 512 normalized inverse-binomial table."""
    if site_count < 2:
        raise ValueError("site_count must be at least two")
    p = np.linspace(0.0, 1.0, LOOKUP_LEVELS, dtype=np.float64)[:, None]
    u = (
        (np.arange(LOOKUP_LEVELS, dtype=np.float64) + 0.5) / LOOKUP_LEVELS
    )[None, :]
    table = stats.binom.ppf(u, site_count, p) / float(site_count)
    return np.nan_to_num(table, nan=0.0, posinf=1.0, neginf=0.0).astype(
        np.float32
    )


def _lookup_binomial_density(
    p: np.ndarray,
    u: np.ndarray,
    table: np.ndarray,
) -> np.ndarray:
    scale = np.float32(LOOKUP_LEVELS - 1)
    fp = np.clip(p, 0.0, 1.0) * scale
    fu = np.clip(u * LOOKUP_LEVELS - 0.5, 0.0, scale)
    p0 = np.floor(fp).astype(np.int32)
    u0 = np.floor(fu).astype(np.int32)
    p1 = np.minimum(p0 + 1, LOOKUP_LEVELS - 1)
    u1 = np.minimum(u0 + 1, LOOKUP_LEVELS - 1)
    wp = fp - p0
    wu = fu - u0
    a = table[p0, u0] * (1.0 - wu) + table[p0, u1] * wu
    b = table[p1, u0] * (1.0 - wu) + table[p1, u1] * wu
    return (a * (1.0 - wp) + b * wp).astype(np.float32)


def _srgb_encode(linear: np.ndarray) -> np.ndarray:
    linear = np.asarray(linear, dtype=np.float32)
    return np.where(
        linear <= 0.0031308,
        12.92 * linear,
        1.055 * np.power(np.maximum(linear, 0.0), 1.0 / 2.4) - 0.055,
    ).astype(np.float32)


def _srgb_decode(encoded: np.ndarray) -> np.ndarray:
    encoded = np.asarray(encoded, dtype=np.float32)
    return np.where(
        encoded <= 0.04045,
        encoded / 12.92,
        np.power((np.maximum(encoded, 0.0) + 0.055) / 1.055, 2.4),
    ).astype(np.float32)


def _transport_luma_without_chroma_modulation(
    rgb: np.ndarray,
    source_luma: np.ndarray,
    target_luma: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Move only luma while keeping the deterministic opponent field fixed.

    A previous implementation reduced chroma whenever the stochastic target
    approached an RGB gamut boundary. Because that reduction was driven by
    the per-frame FSD variate, dark warm pixels acquired sparse coloured
    impulses even though FSD never generated independent RGB noise. Limit the
    *density excursion* to the interval that can carry the existing opponent
    field; never modulate that field with the random variate.
    """
    result = np.empty_like(rgb, dtype=np.float32)
    constrained = 0
    sample_count = int(source_luma.size)
    for y0 in range(0, rgb.shape[0], 128):
        y1 = min(y0 + 128, rgb.shape[0])
        chroma = rgb[y0:y1] - source_luma[y0:y1, :, None]
        requested = target_luma[y0:y1]
        lower = np.maximum(0.0, np.max(-chroma, axis=-1))
        upper = np.minimum(1.0, np.min(1.0 - chroma, axis=-1))
        target = np.clip(requested, lower, upper)
        constrained += int(np.count_nonzero(target != requested))
        result[y0:y1] = target[..., None] + chroma
    # The interval construction is exact apart from float32 round-off.
    np.clip(result, 0.0, 1.0, out=result)
    return result.astype(np.float32, copy=False), constrained / sample_count


def apply_fsd(
    deterministic_linear_rgb: np.ndarray,
    frame_index: int,
    *,
    site_count: int,
    correlation_sigma: float,
    density_strength: float = 1.0,
) -> tuple[np.ndarray, dict[str, float | int | str]]:
    """Form one FSD realization from a deterministic display-linear image."""
    rgb = np.asarray(deterministic_linear_rgb, dtype=np.float32)
    encoded = _srgb_encode(np.clip(rgb, 0.0, 1.0))
    # FSD is a post-observer perceptual-density control, not a second camera or
    # negative model. The recovered finite-site lookup is therefore evaluated
    # in the IEC 61966-2-1 signal domain in which its scalar intensity and the
    # displayed opponent field can be held independently. Evaluating it in
    # linear RGB and encoding later makes a scalar perturbation chromatic.
    luma = np.einsum("...c,c->...", encoded, LUMA, optimize=True).astype(np.float32)
    uniform = correlated_uniform_field(
        rgb.shape[0], rgb.shape[1], frame_index, correlation_sigma
    )
    table = binomial_quantile_table(int(site_count))
    formed_luma = np.empty_like(luma)
    for y0 in range(0, rgb.shape[0], 128):
        y1 = min(y0 + 128, rgb.shape[0])
        p = luma[y0:y1]
        candidate = _lookup_binomial_density(p, uniform[y0:y1], table)
        alpha = np.float32(density_strength) * tone_taper(p)
        formed_luma[y0:y1] = p + alpha * (candidate - p)
    np.clip(formed_luma, 0.0, 1.0, out=formed_luma)
    requested_delta = formed_luma - luma
    encoded_result, gamut_luma_constraint_fraction = (
        _transport_luma_without_chroma_modulation(encoded, luma, formed_luma)
    )
    result = _srgb_decode(encoded_result)
    source_linear_luma = np.einsum("...c,c->...", rgb, LUMA, optimize=True).astype(
        np.float32
    )
    realized_linear_luma = np.einsum(
        "...c,c->...", result, LUMA, optimize=True
    ).astype(np.float32)
    linear_delta = realized_linear_luma - source_linear_luma
    realized_code_luma = np.einsum(
        "...c,c->...", encoded_result, LUMA, optimize=True
    ).astype(np.float32)
    code_delta = realized_code_luma - luma
    stats_record: dict[str, float | int | str] = {
        "pipeline": "Finite-Site Density (FSD)",
        "density_domain": "IEC 61966-2-1 signal after the deterministic observer",
        "site_count": int(site_count),
        "correlation_sigma_native_px": float(correlation_sigma),
        "density_strength": float(density_strength),
        "requested_code_luma_delta_rms": float(
            np.sqrt(np.mean(np.square(requested_delta), dtype=np.float64))
        ),
        "gamut_luma_constraint_fraction": float(gamut_luma_constraint_fraction),
        "code_luma_delta_mean": float(code_delta.mean(dtype=np.float64)),
        "code_luma_delta_rms": float(
            np.sqrt(np.mean(np.square(code_delta), dtype=np.float64))
        ),
        "display_linear_luma_delta_mean": float(
            linear_delta.mean(dtype=np.float64)
        ),
        "display_linear_luma_delta_rms": float(
            np.sqrt(np.mean(np.square(linear_delta), dtype=np.float64))
        ),
        "display_linear_luma_delta_p999_abs": float(
            np.quantile(np.abs(linear_delta), 0.999)
        ),
    }
    return result, stats_record
