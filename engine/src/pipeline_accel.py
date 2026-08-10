"""Experimental quality-preserving CPU kernels for the 5279 pipeline."""

from __future__ import annotations

import numpy as np
from numba import njit, prange


@njit(parallel=True, cache=True)
def linear_rec709_to_oklab_fused(
    rgb: np.ndarray,
    rgb_to_lms: np.ndarray,
    lms_to_lab: np.ndarray,
) -> np.ndarray:
    """Fuse the two OKLab matrix passes without changing float32 order."""
    height, width, _ = rgb.shape
    output = np.empty_like(rgb)
    zero = np.float32(0.0)
    for y in prange(height):
        for x in range(width):
            red = max(rgb[y, x, 0], zero)
            green = max(rgb[y, x, 1], zero)
            blue = max(rgb[y, x, 2], zero)
            l_root = np.cbrt(
                max(
                    red * rgb_to_lms[0, 0]
                    + green * rgb_to_lms[0, 1]
                    + blue * rgb_to_lms[0, 2],
                    zero,
                )
            )
            m_root = np.cbrt(
                max(
                    red * rgb_to_lms[1, 0]
                    + green * rgb_to_lms[1, 1]
                    + blue * rgb_to_lms[1, 2],
                    zero,
                )
            )
            s_root = np.cbrt(
                max(
                    red * rgb_to_lms[2, 0]
                    + green * rgb_to_lms[2, 1]
                    + blue * rgb_to_lms[2, 2],
                    zero,
                )
            )
            for channel in range(3):
                output[y, x, channel] = (
                    l_root * lms_to_lab[channel, 0]
                    + m_root * lms_to_lab[channel, 1]
                    + s_root * lms_to_lab[channel, 2]
                )
    return output


@njit(parallel=True, cache=True)
def linear_rec709_to_oklab_lightness_fused(
    rgb: np.ndarray,
    rgb_to_lms: np.ndarray,
    lightness_row: np.ndarray,
) -> np.ndarray:
    """Evaluate the same fused transform when only OKLab L survives."""
    height, width, _ = rgb.shape
    output = np.empty((height, width), dtype=np.float32)
    zero = np.float32(0.0)
    for y in prange(height):
        for x in range(width):
            red = max(rgb[y, x, 0], zero)
            green = max(rgb[y, x, 1], zero)
            blue = max(rgb[y, x, 2], zero)
            l_root = np.cbrt(
                max(
                    red * rgb_to_lms[0, 0]
                    + green * rgb_to_lms[0, 1]
                    + blue * rgb_to_lms[0, 2],
                    zero,
                )
            )
            m_root = np.cbrt(
                max(
                    red * rgb_to_lms[1, 0]
                    + green * rgb_to_lms[1, 1]
                    + blue * rgb_to_lms[1, 2],
                    zero,
                )
            )
            s_root = np.cbrt(
                max(
                    red * rgb_to_lms[2, 0]
                    + green * rgb_to_lms[2, 1]
                    + blue * rgb_to_lms[2, 2],
                    zero,
                )
            )
            output[y, x] = (
                l_root * lightness_row[0]
                + m_root * lightness_row[1]
                + s_root * lightness_row[2]
            )
    return output


@njit(cache=True, inline="always")
def _interp_scalar(value: np.float32, axis: np.ndarray, table: np.ndarray) -> np.float32:
    if value <= axis[0]:
        return np.float32(table[0])
    last = axis.shape[0] - 1
    if value >= axis[last]:
        return np.float32(table[last])
    upper = np.searchsorted(axis, value)
    lower = upper - 1
    fraction = (value - axis[lower]) / (axis[upper] - axis[lower])
    return np.float32(table[lower] + fraction * (table[upper] - table[lower]))


@njit(parallel=True, cache=True)
def record_density_mix_fused(
    log_exposure: np.ndarray,
    sensitometric_axis: np.ndarray,
    sensitometric_density: np.ndarray,
    fast_centres: np.ndarray,
    speed_offsets: np.ndarray,
    transition_widths: np.ndarray,
    capacity_fractions: np.ndarray,
    dye_record_mix: np.ndarray,
) -> np.ndarray:
    """Fuse H-D interpolation, marginal populations and inter-record mixing."""
    height, width, _ = log_exposure.shape
    output = np.empty_like(log_exposure)
    for y in prange(height):
        for x in range(width):
            neutral_loge = np.float32(
                (log_exposure[y, x, 0] + log_exposure[y, x, 1] + log_exposure[y, x, 2])
                / np.float32(3.0)
            )
            density = np.empty(3, dtype=np.float32)
            neutral_density = np.empty(3, dtype=np.float32)
            marginal = np.empty((3, 3), dtype=np.float32)
            for source in range(3):
                value = log_exposure[y, x, source]
                density[source] = _interp_scalar(
                    value, sensitometric_axis, sensitometric_density[source]
                )
                neutral_density[source] = _interp_scalar(
                    neutral_loge, sensitometric_axis, sensitometric_density[source]
                )
                total = np.float32(0.0)
                for population in range(3):
                    argument = (
                        value - fast_centres[source] - speed_offsets[population]
                    ) / transition_widths[source]
                    argument = min(max(argument, np.float32(-16.0)), np.float32(16.0))
                    activation = np.float32(1.0) / (
                        np.float32(1.0) + np.exp(-argument)
                    )
                    amount = (
                        activation
                        * (np.float32(1.0) - activation)
                        * capacity_fractions[population]
                        / transition_widths[source]
                    )
                    marginal[source, population] = amount
                    total += amount
                inverse_total = np.float32(1.0) / max(total, np.float32(1e-8))
                for population in range(3):
                    marginal[source, population] *= inverse_total

            for destination in range(3):
                mixed = np.float32(0.0)
                for source in range(3):
                    effective = np.float32(0.0)
                    for population in range(3):
                        effective += (
                            marginal[source, population]
                            * dye_record_mix[population, destination, source]
                        )
                    mixed += (density[source] - neutral_density[source]) * effective
                output[y, x, destination] = neutral_density[destination] + mixed
    return output


@njit(parallel=True, cache=True)
def mix_record_departure(
    density: np.ndarray,
    neutral_density: np.ndarray,
    marginal: np.ndarray,
    dye_record_mix: np.ndarray,
) -> np.ndarray:
    """Fuse only the two large einsums after reference interpolation."""
    height, width, _ = density.shape
    output = np.empty_like(density)
    for y in prange(height):
        for x in range(width):
            for destination in range(3):
                mixed = np.float32(0.0)
                for source in range(3):
                    effective = np.float32(0.0)
                    for population in range(3):
                        effective += (
                            marginal[y, x, source, population]
                            * dye_record_mix[population, destination, source]
                        )
                    mixed += (
                        density[y, x, source] - neutral_density[y, x, source]
                    ) * effective
                output[y, x, destination] = neutral_density[y, x, destination] + mixed
    return output


@njit(parallel=True, cache=True)
def camera_cube_trilinear(rgb: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Sample Panasonic's red-fastest cube with one fused, parallel pass."""
    height, width, _ = rgb.shape
    size = lut.shape[0]
    scale = np.float32(size - 1)
    one = np.float32(1.0)
    output = np.empty_like(rgb)
    for y in prange(height):
        for x in range(width):
            sr = min(max(rgb[y, x, 0], np.float32(0.0)), one) * scale
            sg = min(max(rgb[y, x, 1], np.float32(0.0)), one) * scale
            sb = min(max(rgb[y, x, 2], np.float32(0.0)), one) * scale
            r0 = int(sr)
            g0 = int(sg)
            b0 = int(sb)
            r1 = min(r0 + 1, size - 1)
            g1 = min(g0 + 1, size - 1)
            b1 = min(b0 + 1, size - 1)
            fr = sr - np.float32(r0)
            fg = sg - np.float32(g0)
            fb = sb - np.float32(b0)
            for channel in range(3):
                c00 = (
                    lut[b0, g0, r0, channel] * (one - fr)
                    + lut[b0, g0, r1, channel] * fr
                )
                c10 = (
                    lut[b0, g1, r0, channel] * (one - fr)
                    + lut[b0, g1, r1, channel] * fr
                )
                c01 = (
                    lut[b1, g0, r0, channel] * (one - fr)
                    + lut[b1, g0, r1, channel] * fr
                )
                c11 = (
                    lut[b1, g1, r0, channel] * (one - fr)
                    + lut[b1, g1, r1, channel] * fr
                )
                c0 = c00 * (one - fg) + c10 * fg
                c1 = c01 * (one - fg) + c11 * fg
                output[y, x, channel] = c0 * (one - fb) + c1 * fb
    return output


@njit(parallel=True, cache=True)
def density_cube_trilinear(
    density: np.ndarray,
    lut: np.ndarray,
    maximum_density: float,
) -> np.ndarray:
    """Sample a CMY density cube without allocation-heavy advanced indexing."""
    height, width, _ = density.shape
    size = lut.shape[0]
    scale = np.float32(size - 1) / np.float32(maximum_density)
    maximum_index = np.float32(size) - np.float32(1.00001)
    zero = np.float32(0.0)
    one = np.float32(1.0)
    output = np.empty_like(density)
    for y in prange(height):
        for x in range(width):
            sc = min(max(density[y, x, 0] * scale, zero), maximum_index)
            sm = min(max(density[y, x, 1] * scale, zero), maximum_index)
            sy = min(max(density[y, x, 2] * scale, zero), maximum_index)
            c0 = int(sc)
            m0 = int(sm)
            y0 = int(sy)
            c1 = min(c0 + 1, size - 1)
            m1 = min(m0 + 1, size - 1)
            y1 = min(y0 + 1, size - 1)
            fc = sc - np.float32(c0)
            fm = sm - np.float32(m0)
            fy = sy - np.float32(y0)
            for channel in range(3):
                c00 = (
                    lut[c0, m0, y0, channel] * (one - fc)
                    + lut[c1, m0, y0, channel] * fc
                )
                c01 = (
                    lut[c0, m0, y1, channel] * (one - fc)
                    + lut[c1, m0, y1, channel] * fc
                )
                c10 = (
                    lut[c0, m1, y0, channel] * (one - fc)
                    + lut[c1, m1, y0, channel] * fc
                )
                c11 = (
                    lut[c0, m1, y1, channel] * (one - fc)
                    + lut[c1, m1, y1, channel] * fc
                )
                c0y = c00 * (one - fy) + c01 * fy
                c1y = c10 * (one - fy) + c11 * fy
                output[y, x, channel] = c0y * (one - fm) + c1y * fm
    return output


@njit(parallel=True, cache=True)
def signed_density_cube_trilinear(
    total_density: np.ndarray,
    lut: np.ndarray,
    dmin_rgb: np.ndarray,
    net_minimum: float,
    net_maximum: float,
) -> np.ndarray:
    """Sample a signed total-record-density cube without advanced indexing.

    This preserves the arithmetic and interpolation order used by
    ``sample_record_density_delta_lut``.  Unlike ``density_cube_trilinear``,
    the cube's domain begins below D-min so print-through density departures
    remain representable.
    """
    height, width, _ = total_density.shape
    size = lut.shape[0]
    # NumPy evaluates the scalar ratio in Python float precision, then casts it
    # to the float32 array dtype during multiplication.
    scale = np.float32((size - 1) / (net_maximum - net_minimum))
    maximum_index = np.float32(size) - np.float32(1.00001)
    minimum = np.float32(net_minimum)
    zero = np.float32(0.0)
    one = np.float32(1.0)
    output = np.empty_like(total_density)
    for y in prange(height):
        for x in range(width):
            sr = (total_density[y, x, 0] - dmin_rgb[0] - minimum) * scale
            sg = (total_density[y, x, 1] - dmin_rgb[1] - minimum) * scale
            sb = (total_density[y, x, 2] - dmin_rgb[2] - minimum) * scale
            sr = min(max(sr, zero), maximum_index)
            sg = min(max(sg, zero), maximum_index)
            sb = min(max(sb, zero), maximum_index)
            r0 = int(sr)
            g0 = int(sg)
            b0 = int(sb)
            r1 = min(r0 + 1, size - 1)
            g1 = min(g0 + 1, size - 1)
            b1 = min(b0 + 1, size - 1)
            fr = sr - np.float32(r0)
            fg = sg - np.float32(g0)
            fb = sb - np.float32(b0)
            for channel in range(3):
                c00 = (
                    lut[r0, g0, b0, channel] * (one - fr)
                    + lut[r1, g0, b0, channel] * fr
                )
                c10 = (
                    lut[r0, g1, b0, channel] * (one - fr)
                    + lut[r1, g1, b0, channel] * fr
                )
                c01 = (
                    lut[r0, g0, b1, channel] * (one - fr)
                    + lut[r1, g0, b1, channel] * fr
                )
                c11 = (
                    lut[r0, g1, b1, channel] * (one - fr)
                    + lut[r1, g1, b1, channel] * fr
                )
                output[y, x, channel] = (
                    (c00 * (one - fg) + c10 * fg) * (one - fb)
                    + (c01 * (one - fg) + c11 * fg) * fb
                )
    return output


@njit(parallel=True, cache=True)
def h61_density_cube_trilinear(
    total_density: np.ndarray,
    lut: np.ndarray,
    dmin_rgb: np.ndarray,
    net_minimum: float,
    net_maximum: float,
) -> np.ndarray:
    """Exact fused sampler for the historical H-61 interpolation order.

    The H-61 calibration predates ``sample_record_density_delta_lut`` and
    interpolates red, then blue, then green. The two trilinear forms are
    algebraically equivalent but not bit-equivalent in float32. Retaining that
    association lets Production remove the allocation-heavy advanced indexing
    without changing a single output sample.
    """
    height, width, _ = total_density.shape
    size = lut.shape[0]
    scale = np.float32((size - 1) / (net_maximum - net_minimum))
    maximum_index = np.float32(size) - np.float32(1.00001)
    minimum = np.float32(net_minimum)
    zero = np.float32(0.0)
    one = np.float32(1.0)
    output = np.empty_like(total_density)
    for y in prange(height):
        for x in range(width):
            sr = (total_density[y, x, 0] - dmin_rgb[0] - minimum) * scale
            sg = (total_density[y, x, 1] - dmin_rgb[1] - minimum) * scale
            sb = (total_density[y, x, 2] - dmin_rgb[2] - minimum) * scale
            sr = min(max(sr, zero), maximum_index)
            sg = min(max(sg, zero), maximum_index)
            sb = min(max(sb, zero), maximum_index)
            r0 = int(sr)
            g0 = int(sg)
            b0 = int(sb)
            r1 = min(r0 + 1, size - 1)
            g1 = min(g0 + 1, size - 1)
            b1 = min(b0 + 1, size - 1)
            fr = sr - np.float32(r0)
            fg = sg - np.float32(g0)
            fb = sb - np.float32(b0)
            for channel in range(3):
                c00 = (
                    lut[r0, g0, b0, channel] * (one - fr)
                    + lut[r1, g0, b0, channel] * fr
                )
                c01 = (
                    lut[r0, g0, b1, channel] * (one - fr)
                    + lut[r1, g0, b1, channel] * fr
                )
                c10 = (
                    lut[r0, g1, b0, channel] * (one - fr)
                    + lut[r1, g1, b0, channel] * fr
                )
                c11 = (
                    lut[r0, g1, b1, channel] * (one - fr)
                    + lut[r1, g1, b1, channel] * fr
                )
                c0b = c00 * (one - fb) + c01 * fb
                c1b = c10 * (one - fb) + c11 * fb
                output[y, x, channel] = c0b * (one - fg) + c1b * fg
    return output


@njit(parallel=True, cache=True)
def factor_table_interp(luma: np.ndarray, axis: np.ndarray, table: np.ndarray) -> np.ndarray:
    """Parallel equivalent of three np.interp calls for a shared luma axis."""
    height, width = luma.shape
    last = axis.shape[0] - 1
    output = np.empty((height, width, 3), dtype=np.float32)
    for y in prange(height):
        for x in range(width):
            value = luma[y, x]
            if value <= axis[0]:
                lower = 0
                upper = 0
                fraction = 0.0
            elif value >= axis[last]:
                lower = last
                upper = last
                fraction = 0.0
            else:
                upper = np.searchsorted(axis, value)
                lower = upper - 1
                fraction = (
                    np.float64(value) - np.float64(axis[lower])
                ) / (
                    np.float64(axis[upper]) - np.float64(axis[lower])
                )
            for channel in range(3):
                if lower == upper:
                    result = np.float64(table[lower, channel])
                else:
                    result = (
                        np.float64(table[lower, channel])
                        + fraction
                        * (
                            np.float64(table[upper, channel])
                            - np.float64(table[lower, channel])
                        )
                    )
                output[y, x, channel] = np.float32(result)
    return output


@njit(parallel=True, cache=True)
def factor_table_interp_float64(
    luma: np.ndarray, axis: np.ndarray, table: np.ndarray
) -> np.ndarray:
    """Exact float64 factors for a reference path that multiplies before cast."""
    height, width = luma.shape
    last = axis.shape[0] - 1
    output = np.empty((height, width, 3), dtype=np.float64)
    for y in prange(height):
        for x in range(width):
            value = luma[y, x]
            if value <= axis[0]:
                lower = 0
                upper = 0
                fraction = 0.0
            elif value >= axis[last]:
                lower = last
                upper = last
                fraction = 0.0
            else:
                upper = np.searchsorted(axis, value)
                lower = upper - 1
                fraction = (
                    np.float64(value) - np.float64(axis[lower])
                ) / (
                    np.float64(axis[upper]) - np.float64(axis[lower])
                )
            for channel in range(3):
                if lower == upper:
                    output[y, x, channel] = np.float64(table[lower, channel])
                else:
                    output[y, x, channel] = (
                        np.float64(table[lower, channel])
                        + fraction
                        * (
                            np.float64(table[upper, channel])
                            - np.float64(table[lower, channel])
                        )
                    )
    return output


@njit(parallel=True, cache=True)
def channel_table_interp(
    values: np.ndarray, axis: np.ndarray, channel_tables: np.ndarray
) -> np.ndarray:
    """Exact float32 equivalent of three channel-specific np.interp calls."""
    height, width, _ = values.shape
    last = axis.shape[0] - 1
    output = np.empty_like(values)
    for y in prange(height):
        for x in range(width):
            for channel in range(3):
                value = values[y, x, channel]
                if value <= axis[0]:
                    result = np.float64(channel_tables[channel, 0])
                elif value >= axis[last]:
                    result = np.float64(channel_tables[channel, last])
                else:
                    upper = np.searchsorted(axis, value)
                    lower = upper - 1
                    fraction = (
                        np.float64(value) - np.float64(axis[lower])
                    ) / (
                        np.float64(axis[upper]) - np.float64(axis[lower])
                    )
                    result = (
                        np.float64(channel_tables[channel, lower])
                        + fraction
                        * (
                            np.float64(channel_tables[channel, upper])
                            - np.float64(channel_tables[channel, lower])
                        )
                    )
                output[y, x, channel] = np.float32(result)
    return output


@njit(parallel=True, cache=True)
def preserve_luma_and_compress_gamut(
    rgb: np.ndarray,
    target_luma: np.ndarray,
) -> np.ndarray:
    """Fused exact V31 luma-preserving Rec.709 gamut boundary."""
    height, width, _ = rgb.shape
    output = np.empty_like(rgb)
    w0 = np.float32(0.2126)
    w1 = np.float32(0.7152)
    w2 = np.float32(0.0722)
    zero = np.float32(0.0)
    one = np.float32(1.0)
    epsilon = np.float32(1e-8)
    infinity = np.float32(np.inf)
    for y in prange(height):
        for x in range(width):
            current_luma = (
                rgb[y, x, 0] * w0
                + rgb[y, x, 1] * w1
                + rgb[y, x, 2] * w2
            )
            target = target_luma[y, x]
            shift = target - current_luma
            d0 = rgb[y, x, 0] + shift - target
            d1 = rgb[y, x, 1] + shift - target
            d2 = rgb[y, x, 2] + shift - target
            scale = one
            for delta in (d0, d1, d2):
                positive_limit = (
                    (one - target) / max(delta, epsilon)
                    if delta > epsilon
                    else infinity
                )
                negative_limit = (
                    target / max(-delta, epsilon)
                    if delta < -epsilon
                    else infinity
                )
                scale = min(scale, positive_limit, negative_limit)
            output[y, x, 0] = min(max(target + d0 * scale, zero), one)
            output[y, x, 1] = min(max(target + d1 * scale, zero), one)
            output[y, x, 2] = min(max(target + d2 * scale, zero), one)
    return output


@njit(parallel=True, cache=True)
def compress_unit_gamut_from_luma(rgb: np.ndarray, luma: np.ndarray) -> np.ndarray:
    """Fuse chroma-bound calculations while accepting reference NumPy luma."""
    height, width, _ = rgb.shape
    output = np.empty_like(rgb)
    zero = np.float32(0.0)
    one = np.float32(1.0)
    epsilon = np.float32(1e-6)
    for y in prange(height):
        for x in range(width):
            luminance = min(max(luma[y, x], zero), one)
            c0 = rgb[y, x, 0] - luminance
            c1 = rgb[y, x, 1] - luminance
            c2 = rgb[y, x, 2] - luminance
            upper_excursion = max(c0, c1, c2)
            lower_excursion = -min(c0, c1, c2)
            if upper_excursion > epsilon:
                upper_scale = (one - luminance) / max(upper_excursion, epsilon)
            else:
                upper_scale = one
            if lower_excursion > epsilon:
                lower_scale = luminance / max(lower_excursion, epsilon)
            else:
                lower_scale = one
            scale = min(one, upper_scale, lower_scale)
            output[y, x, 0] = min(max(luminance + c0 * scale, zero), one)
            output[y, x, 1] = min(max(luminance + c1 * scale, zero), one)
            output[y, x, 2] = min(max(luminance + c2 * scale, zero), one)
    return output
