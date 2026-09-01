#!/usr/bin/env python3
"""Audit an active-set-aware Status-M to 2383 printer-density observer.

Uniform trilinear interpolation crosses the nonnegative-CMY active-set
boundary and therefore converges slowly in maximum error.  This audit keeps a
small, fast cube for smooth cells and performs one projected Gauss-Newton
correction only in cells whose eight corners disagree about the active set.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

import emulsion_experiment as e
import v72_profile
from build_v87_printer_density_lut import exact_printer_density


def trilinear(lut: np.ndarray, source: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    size = int(lut.shape[0])
    points = np.asarray(source, dtype=np.float64).reshape(-1, 3)
    scaled = np.clip(
        points * ((size - 1) / e.NEGATIVE_5279_MAX_RECORD_DENSITY),
        0.0,
        size - 1.00001,
    )
    lower = np.floor(scaled).astype(np.int16)
    upper = np.minimum(lower + 1, size - 1)
    fraction = scaled - lower
    c0, m0, y0 = lower.T
    c1, m1, y1 = upper.T
    fc, fm, fy = fraction[:, 0:1], fraction[:, 1:2], fraction[:, 2:3]
    c00 = lut[c0, m0, y0] * (1.0 - fc) + lut[c1, m0, y0] * fc
    c01 = lut[c0, m0, y1] * (1.0 - fc) + lut[c1, m0, y1] * fc
    c10 = lut[c0, m1, y0] * (1.0 - fc) + lut[c1, m1, y0] * fc
    c11 = lut[c0, m1, y1] * (1.0 - fc) + lut[c1, m1, y1] * fc
    c0y = c00 * (1.0 - fy) + c01 * fy
    c1y = c10 * (1.0 - fy) + c11 * fy
    return c0y * (1.0 - fm) + c1y * fm, lower


def active_set_risk(cmy_lut: np.ndarray, threshold: float = 1e-6) -> np.ndarray:
    size = int(cmy_lut.shape[0])
    active = np.asarray(cmy_lut) > threshold
    all_active = np.ones((size - 1, size - 1, size - 1, 3), dtype=bool)
    any_active = np.zeros_like(all_active)
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                corner = active[
                    red : red + size - 1,
                    green : green + size - 1,
                    blue : blue + size - 1,
                ]
                all_active &= corner
                any_active |= corner
    return np.any(all_active != any_active, axis=-1)


def one_projected_newton(target: np.ndarray, initial: np.ndarray) -> np.ndarray:
    weights = e._negative_5279_status_m_weights().astype(np.float64)
    dmin, spectra = e._negative_5279_status_m_model_spectra()
    dmin = dmin.astype(np.float64)
    spectra = spectra.astype(np.float64)
    coefficients = np.asarray(initial, dtype=np.float64).copy()
    with np.errstate(all="ignore"):
        base = -np.log10(np.maximum(np.power(10.0, -dmin) @ weights, 1e-30))
        transmission = np.power(
            10.0, -(dmin[None, :] + coefficients @ spectra.T)
        )
        integrated = np.maximum(transmission @ weights, 1e-30)
        density = -np.log10(integrated) - base
        jacobian = np.einsum(
            "nl,lj,lk->njk", transmission, weights, spectra
        ) / integrated[:, :, None]
        normal = np.einsum("nji,njk->nik", jacobian, jacobian)
        normal[:, np.arange(3), np.arange(3)] += 1e-8
        gradient = np.einsum("nji,nj->ni", jacobian, density - target)
        step = -np.linalg.solve(normal, gradient[..., None])[..., 0]
        damping = np.maximum(
            1.0, np.max(np.abs(step), axis=1, keepdims=True) / 0.5
        )
    return np.clip(coefficients + step / damping, 0.0, 12.0)


def printer_density_from_cmy(cmy: np.ndarray) -> np.ndarray:
    spectra = np.asarray(
        e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float64
    )
    lamp = np.asarray(
        e._blackbody_spd(e.NEGATIVE_DYE_WAVELENGTHS_NM, 3200.0),
        dtype=np.float64,
    )
    sensitivity = np.power(
        10.0, np.asarray(e.PRINT_2383_LOG_SENSITIVITY_CMY, dtype=np.float64)
    )
    weights = lamp[:, None] * sensitivity
    weights /= np.sum(weights, axis=0, keepdims=True)
    with np.errstate(all="ignore"):
        spectral_density = (
            np.asarray(e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY, dtype=np.float64)[
                None, :
            ]
            + np.asarray(cmy, dtype=np.float64) @ spectra.T
        )
        transmission = np.power(10.0, -np.clip(spectral_density, 0.0, 16.0))
        result = -np.log10(np.maximum(transmission @ weights, 1e-12))
    return result


def audit_points() -> np.ndarray:
    rng = np.random.default_rng(5279)
    levels = np.asarray(
        [0.0, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0],
        dtype=np.float32,
    )
    red, green, blue = np.meshgrid(levels, levels, levels, indexing="ij")
    grid = np.stack([red, green, blue], axis=-1).reshape(-1, 3)
    random = np.power(10.0, rng.uniform(-4.0, 1.0, size=(10_000, 3))).astype(
        np.float32
    )
    random[rng.random(random.shape) < 0.08] = 0.0
    film = np.concatenate([grid, random], axis=0)
    total = e.develop_5279_record_density(e.film_records_from_rgb(film))
    net = np.maximum(total - e.SENSITO_DMIN_RGB, 0.0).astype(np.float64)
    indices = rng.integers(0, net.shape[0], size=5_000)
    perturbation = rng.normal(
        0.0, np.asarray([0.03, 0.03, 0.05]), size=(5_000, 3)
    )
    return np.clip(
        np.concatenate([net, net[indices] + perturbation], axis=0),
        0.0,
        e.NEGATIVE_5279_MAX_RECORD_DENSITY,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("printer_lut", type=Path)
    parser.add_argument("cmy_lut", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    v72_profile.apply(e)
    printer_lut = np.load(args.printer_lut, mmap_mode="r")
    cmy_lut = np.load(args.cmy_lut, mmap_mode="r")
    if printer_lut.shape != cmy_lut.shape:
        raise ValueError("printer and CMY LUT shapes differ")
    if not np.isfinite(printer_lut).all() or not np.isfinite(cmy_lut).all():
        raise ValueError("a candidate LUT contains non-finite values")

    points = audit_points()
    approximate, lower = trilinear(printer_lut, points)
    initial, _ = trilinear(cmy_lut, points)
    risk = active_set_risk(cmy_lut)
    flagged = risk[lower[:, 0], lower[:, 1], lower[:, 2]]
    started = time.perf_counter()
    approximate[flagged] = printer_density_from_cmy(
        one_projected_newton(points[flagged], initial[flagged])
    )
    hybrid_seconds = time.perf_counter() - started
    exact = exact_printer_density(points).astype(np.float64)
    error = approximate - exact
    absolute = np.abs(error)
    worst = np.unravel_index(np.argmax(absolute), absolute.shape)
    report = {
        "policy": "trilinear_plus_one_projected_newton_on_active_set_cells",
        "lut_size": int(cmy_lut.shape[0]),
        "point_count": int(points.shape[0]),
        "risk_cell_fraction": float(np.mean(risk)),
        "flagged_point_fraction": float(np.mean(flagged)),
        "hybrid_correction_seconds": hybrid_seconds,
        "maximum_absolute_printer_density_error": float(absolute[worst]),
        "p99_absolute_printer_density_error": float(np.percentile(absolute, 99)),
        "rms_printer_density_error": float(np.sqrt(np.mean(np.square(error)))),
        "worst_status_m_net_density": points[worst[0]].tolist(),
        "worst_output_record": ("red", "green", "blue")[worst[1]],
        "worst_point_was_corrected": bool(flagged[worst[0]]),
        "quality_gate_maximum_density_error": 0.001,
        "quality_gate_pass": bool(float(absolute[worst]) < 0.001),
    }
    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
