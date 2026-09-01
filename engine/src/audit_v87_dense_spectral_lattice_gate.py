#!/usr/bin/env python3
"""V87: close the V86 shadow printer-density gate with dense spectral lattices.

V86 found that the runtime 29-cube joint Status-M -> 2383 printer-density
lattice misses the direct V61 spectral integration by up to about 0.014 D in
the toe.  V86 set a gate: replace or densify that stage, rebuild both observers
from the same direct spectral authority, and require shadow error below
0.001 D and mid-scale drift below 0.001 D before any new image release.

This audit executes that gate on Linux CPU with the V72 evidence-minimal
profile.  It

1. reproduces the 29-cube error against the direct spectral evaluation on the
   neutral H-D locus, on every +-1 sigma record perturbation, on random
   densities and on a complete formed (stochastic) synthetic negative;
2. builds uniform and toe-refined (power-spaced) lattices of several sizes and
   measures their worst error on the same probes;
3. audits the second, previously unexamined spectral lattice: the 25-cube 2383
   Status-A -> xenon/CIE projection LUT, whose 0.17 D cells interpolate
   transmission-space RGB;
4. rebuilds the projection and scan observers from the direct authority and
   measures the display-colour consequence of the runtime lattices in OKLab,
   answering V86's inferred "cyan/green shadow" direction with a measurement.

Everything is deterministic.  Results are written as JSON next to the other
research runs.  No profile pixels are changed by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import emulsion_experiment as e  # noqa: E402
import v72_profile  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "studio"))
from film5279 import spectral as studio_spectral  # noqa: E402

ENGINE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ENGINE_ROOT / "research_runs" / "v87_dense_spectral_lattice_gate"
GATE_DENSITY = 0.001


# --------------------------------------------------------------------------
# Direct spectral authorities (no lattice)
# --------------------------------------------------------------------------


def direct_printer_density(status_m_net_density: np.ndarray) -> np.ndarray:
    """Joint V61 Status-M inverse followed by 3200 K / 2383 spectral printing.

    The heavy sweeps use the studio's Numba kernel of the same projected
    Gauss-Newton equations; ``legacy_direct_printer_density`` below is the
    original NumPy engine path and the audit reports their agreement.
    """
    return studio_spectral.printer_density_direct(status_m_net_density)


def legacy_direct_printer_density(status_m_net_density: np.ndarray) -> np.ndarray:
    """Original engine solver and printer integration (slow reference)."""
    source = np.asarray(status_m_net_density, dtype=np.float64)
    original_shape = source.shape
    flat = source.reshape(-1, 3)
    spectra = np.asarray(e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float64)
    lamp = np.asarray(e._blackbody_spd(e.NEGATIVE_DYE_WAVELENGTHS_NM, 3200.0), dtype=np.float64)
    sensitivity = np.power(10.0, np.asarray(e.PRINT_2383_LOG_SENSITIVITY_CMY, dtype=np.float64))
    weights = lamp[:, None] * sensitivity
    weights /= np.sum(weights, axis=0, keepdims=True)
    dmin = np.asarray(e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY, dtype=np.float64)
    result = np.empty_like(flat, dtype=np.float32)
    for start in range(0, flat.shape[0], 65536):
        stop = min(start + 65536, flat.shape[0])
        cmy = e.solve_5279_analytical_cmy_from_status_m_net_density(flat[start:stop])
        spectral_density = dmin[None, :] + np.asarray(cmy, dtype=np.float64) @ spectra.T
        transmission = np.power(10.0, -np.clip(spectral_density, 0.0, 16.0))
        result[start:stop] = -np.log10(np.maximum(transmission @ weights, 1e-12))
    return result.reshape(original_shape)


def direct_solve_residual(status_m_net_density: np.ndarray) -> np.ndarray:
    """Forward Status-M of the solved CMY minus the requested Status-M."""
    flat = np.asarray(status_m_net_density, dtype=np.float64).reshape(-1, 3)
    cmy = e.solve_5279_analytical_cmy_from_status_m_net_density(flat)
    forward = e.negative_5279_status_m_net_density_from_analytical_cmy(cmy)
    return (forward.astype(np.float64) - np.maximum(flat, 0.0)).reshape(np.asarray(status_m_net_density).shape)


def _projection_integration() -> dict[str, np.ndarray]:
    """Return the exact spectral projection operator used by the 2383 LUT."""
    wavelengths, cmf = e._cie_1931_xyz_official_1nm()
    dye = np.stack(
        [
            np.interp(wavelengths, e.PRINT_DYE_WAVELENGTHS_NM, e.PRINT_DYE_CMY_SPECTRAL_DENSITY[:, c])
            for c in range(3)
        ],
        axis=1,
    )
    illuminant = np.interp(wavelengths, e.PRINT_DYE_WAVELENGTHS_NM, e.KODAK_XENON_PROJECTOR_RELATIVE_SPD)
    integration_weights = np.ones(wavelengths.size, dtype=np.float64)
    integration_weights[[0, -1]] = 0.5
    weighted_cmf = illuminant[:, None] * cmf * integration_weights[:, None]
    base = np.interp(wavelengths, e.PRINT_DYE_WAVELENGTHS_NM, e.PRINT_2383_DMIN_SPECTRAL_DENSITY)
    white_xyz = np.sum(weighted_cmf, axis=0)
    d65 = np.array([0.95047, 1.0, 1.08883])
    source_white = white_xyz / white_xyz[1]
    bradford = np.array(
        [[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]]
    )
    adaptation = (
        np.linalg.inv(bradford)
        @ np.diag((bradford @ d65) / np.maximum(bradford @ source_white, 1e-8))
        @ bradford
    )
    return {
        "dye": dye,
        "weighted_cmf": weighted_cmf,
        "base": base,
        "white_y": white_xyz[1],
        "adaptation": adaptation,
    }


_PROJECTION_OPERATOR: dict[str, np.ndarray] | None = None


def direct_projection_rgb(print_density_rgb: np.ndarray) -> np.ndarray:
    """Exact per-point evaluation of the spectral 2383 -> xenon -> CIE path."""
    global _PROJECTION_OPERATOR
    if _PROJECTION_OPERATOR is None:
        _PROJECTION_OPERATOR = _projection_integration()
    op = _PROJECTION_OPERATOR
    source = np.asarray(print_density_rgb, dtype=np.float64)
    flat = np.clip(source.reshape(-1, 3), 0.0, e.PRINT_2383_DMAX)
    axes = e._print_2383_analytical_amount_axes(np.linspace(0.0, e.PRINT_2383_DMAX, 4097, dtype=np.float32))
    amount_axis = np.linspace(0.0, e.PRINT_2383_DMAX, 4097)
    cmy = np.stack([np.interp(flat[:, c], amount_axis, axes[c]) for c in range(3)], axis=1)
    result = np.empty_like(flat, dtype=np.float32)
    for start in range(0, flat.shape[0], 32768):
        stop = min(start + 32768, flat.shape[0])
        spectral = np.clip(cmy[start:stop] @ op["dye"].T + op["base"][None, :], 0.0, 16.0)
        xyz = np.power(10.0, -spectral) @ op["weighted_cmf"] / op["white_y"]
        xyz = xyz @ op["adaptation"].T
        result[start:stop] = xyz @ np.asarray(e.XYZ_D65_TO_REC709, dtype=np.float64).T
    return result.reshape(source.shape)


# --------------------------------------------------------------------------
# Lattices
# --------------------------------------------------------------------------


class Lattice:
    """Trilinear lattice over one shared, possibly non-uniform, density axis."""

    def __init__(self, name: str, axis: np.ndarray, evaluate) -> None:
        self.name = name
        self.axis = np.asarray(axis, dtype=np.float64)
        size = self.axis.size
        a, b, c = np.meshgrid(self.axis, self.axis, self.axis, indexing="ij")
        target = np.stack([a, b, c], axis=-1).reshape(-1, 3)
        started = time.perf_counter()
        self.values = evaluate(target).reshape(size, size, size, 3).astype(np.float32)
        self.build_seconds = time.perf_counter() - started
        self.size = size
        self.index_axis = np.arange(size, dtype=np.float64)

    def sample(self, density: np.ndarray) -> np.ndarray:
        source = np.asarray(density, dtype=np.float64)
        flat = source.reshape(-1, 3)
        result = np.empty_like(flat, dtype=np.float32)
        size = self.size
        for start in range(0, flat.shape[0], 500_000):
            stop = min(start + 500_000, flat.shape[0])
            chunk = flat[start:stop]
            scaled = np.stack(
                [np.interp(chunk[:, c], self.axis, self.index_axis) for c in range(3)], axis=1
            )
            scaled = np.clip(scaled, 0.0, size - 1.00001)
            lower = np.floor(scaled).astype(np.int32)
            fraction = (scaled - lower).astype(np.float32)
            upper = np.minimum(lower + 1, size - 1)
            lut = self.values
            c0, m0, y0 = lower[:, 0], lower[:, 1], lower[:, 2]
            c1, m1, y1 = upper[:, 0], upper[:, 1], upper[:, 2]
            fc, fm, fy = fraction[:, 0:1], fraction[:, 1:2], fraction[:, 2:3]
            c00 = lut[c0, m0, y0] * (1 - fc) + lut[c1, m0, y0] * fc
            c01 = lut[c0, m0, y1] * (1 - fc) + lut[c1, m0, y1] * fc
            c10 = lut[c0, m1, y0] * (1 - fc) + lut[c1, m1, y0] * fc
            c11 = lut[c0, m1, y1] * (1 - fc) + lut[c1, m1, y1] * fc
            result[start:stop] = (c00 * (1 - fy) + c01 * fy) * (1 - fm) + (c10 * (1 - fy) + c11 * fy) * fm
        return result.reshape(source.shape)


def uniform_axis(size: int, maximum: float) -> np.ndarray:
    return np.linspace(0.0, maximum, size)


def power_axis(size: int, maximum: float, power: float) -> np.ndarray:
    return maximum * np.power(np.linspace(0.0, 1.0, size), power)


# --------------------------------------------------------------------------
# Probes
# --------------------------------------------------------------------------


def neutral_locus(log_exposure: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Neutral net Status-M density and Kodak marginal RMS along the H-D locus."""
    le = np.repeat(np.asarray(log_exposure, dtype=np.float32)[:, None], 3, axis=1)
    total = e.record_densities_from_log_exposure(le)
    net = np.maximum(total - e.SENSITO_DMIN_RGB, 0.0)
    sigma = e.published_5279_granularity_sigma(le)
    return net.astype(np.float64), sigma.astype(np.float64)


SIGN_COMBOS = np.array([[i, j, k] for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)], dtype=np.float64)


def perturbation_cloud(net: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    """Every +-1 sigma sign combination around each neutral point (27 each)."""
    cloud = net[:, None, :] + SIGN_COMBOS[None, :, :] * sigma[:, None, :]
    return np.maximum(cloud, 0.0)


def synthetic_scene(width: int = 480, height: int = 270) -> np.ndarray:
    """Deterministic scene-linear BT.2020 test frame with a wide tonal span."""
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    u = x / (width - 1)
    v = y / (height - 1)
    stops = -7.0 + 10.0 * u
    gray = 0.18 * np.power(2.0, stops)
    frame = np.repeat(gray[..., None], 3, axis=2)
    patches = np.array(
        [
            [0.45, 0.06, 0.05], [0.05, 0.35, 0.08], [0.05, 0.08, 0.45], [0.55, 0.45, 0.06],
            [0.08, 0.40, 0.40], [0.45, 0.08, 0.40], [0.42, 0.30, 0.22], [0.12, 0.10, 0.07],
        ],
        dtype=np.float32,
    )
    band = (v > 0.55) & (v < 0.85)
    index = np.clip((u * 8).astype(int), 0, 7)
    frame[band] = patches[index[band]] * (0.15 + 3.0 * v[band][:, None])
    rng = np.random.default_rng(87)
    frame *= 1.0 + 0.02 * rng.standard_normal(frame.shape).astype(np.float32)
    frame[v > 0.85] = np.stack([gray, gray * 0.6, gray * 0.35], axis=-1)[v > 0.85] * 2.0
    return np.maximum(frame, 0.0).astype(np.float32)


def formed_synthetic_negative(scene: np.ndarray) -> dict[str, np.ndarray]:
    """Mean and formed V72 negative plus the V49 common-density publication."""
    film_rgb = e.scene_to_5279_film_rgb(scene, 0.45, "avfoundation_bt2020", True, "photochemical")
    records = e.film_records_from_rgb(film_rgb)
    log_exposure = np.log10(np.maximum(records, 1e-8)) - 1.0
    activations = e.subemulsion_activation_probabilities(log_exposure)
    mean = e.develop_5279_record_density_from_log_exposure(log_exposure, precomputed_activations=activations)
    formed = e.form_5279_multilayer_record_density(
        records, 0, 1.0, 1,
        precomputed_mean_density=mean,
        precomputed_log_exposure=log_exposure,
        precomputed_activations=activations,
    )
    sigma = np.maximum(e.published_5279_granularity_sigma(log_exposure), 1e-6)
    residual = formed - mean
    common = np.sum(residual / sigma, axis=2, keepdims=True) / np.sqrt(3.0) * np.min(sigma, axis=2, keepdims=True)
    formed_common = np.maximum(mean + common, 0.0).astype(np.float32)
    return {"mean": mean, "formed": formed, "formed_common": formed_common, "log_exposure": log_exposure}


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def error_summary(candidate: np.ndarray, reference: np.ndarray) -> dict[str, object]:
    diff = np.asarray(candidate, dtype=np.float64) - np.asarray(reference, dtype=np.float64)
    magnitude = np.abs(diff).reshape(-1, 3)
    return {
        "max_abs": float(magnitude.max()),
        "max_abs_rgb": [float(v) for v in magnitude.max(axis=0)],
        "p999_abs": float(np.percentile(magnitude, 99.9)),
        "p99_abs": float(np.percentile(magnitude, 99.0)),
        "mean_abs": float(magnitude.mean()),
        "mean_signed_rgb": [float(v) for v in diff.reshape(-1, 3).mean(axis=0)],
        "samples": int(magnitude.shape[0]),
    }


def oklab(rgb: np.ndarray) -> np.ndarray:
    return e.linear_rec709_to_oklab(np.asarray(rgb, dtype=np.float32)).astype(np.float64)


def hue_degrees(ab: np.ndarray) -> float:
    return float(np.degrees(np.arctan2(ab[1], ab[0])) % 360.0)


# --------------------------------------------------------------------------
# Observer graphs under a swappable printer-density authority
# --------------------------------------------------------------------------


def install_printer_density(function) -> None:
    """Swap the joint spectral printer stage and rebuild every derived table."""
    e.apply_5279_to_2383_printer_density_lut = function
    e.refresh_5279_spectral_observer_caches()


def runtime_29_cube(net: np.ndarray) -> np.ndarray:
    return ORIGINAL_RUNTIME(net)


def projection_view(total_density: np.ndarray) -> np.ndarray:
    """Physical 2383 / xenon / CIE observer with the neutral-derived display curve."""
    return e.apply_2383_monitor_neutral_curve(e._render_2383_projection_uncalibrated(total_density))


def scan_view(total_density: np.ndarray) -> np.ndarray:
    """Pointwise Cineon scan observer with the Blu-ray finish and gray balance."""
    scan = e.finish_cineon_scan_for_bluray(e.render_cineon_scan_master_from_record_density(total_density))
    return e.neutralize_spirit_finished_gray_scale(e.compress_oklab_chroma_to_rec709(scan))


def observe(total_density: np.ndarray) -> dict[str, np.ndarray]:
    source = np.asarray(total_density, dtype=np.float32)
    if source.ndim == 2:
        source = source[None, ...]
    return {"projection": projection_view(source), "scan": scan_view(source)}


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--random-samples", type=int, default=200_000)
    parser.add_argument("--largest", type=int, default=129)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    wall_started = time.perf_counter()

    v72_profile.apply(e)
    global ORIGINAL_RUNTIME
    ORIGINAL_RUNTIME = e.apply_5279_to_2383_printer_density_lut
    assert e.NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY == "legacy_29_cube_trilinear"
    report: dict[str, object] = {
        "audit": "V87 dense spectral lattice gate",
        "profile": "v72",
        "gate_density": GATE_DENSITY,
        "machine": {"numpy": np.__version__},
    }

    # ---- probes -----------------------------------------------------------
    log_exposure = np.round(np.arange(-4.0, 0.0 + 1e-6, 0.01), 4)
    net, sigma = neutral_locus(log_exposure)
    cloud = perturbation_cloud(net, sigma)  # (n, 27, 3)
    toe = log_exposure <= -2.5
    rng = np.random.default_rng(870)
    random_uniform = rng.uniform(0.0, e.NEGATIVE_5279_MAX_RECORD_DENSITY, size=(args.random_samples, 3))
    picks = rng.integers(0, net.shape[0], size=args.random_samples)
    random_near_neutral = np.clip(net[picks] + rng.normal(0.0, 0.15, size=(args.random_samples, 3)), 0.0, e.NEGATIVE_5279_MAX_RECORD_DENSITY)
    scene = synthetic_scene()
    negative = formed_synthetic_negative(scene)
    formed_net = np.maximum(negative["formed_common"] - e.SENSITO_DMIN_RGB, 0.0).reshape(-1, 3).astype(np.float64)
    formed_independent_net = np.maximum(negative["formed"] - e.SENSITO_DMIN_RGB, 0.0).reshape(-1, 3).astype(np.float64)

    probes = {
        "neutral_locus": net,
        "neutral_locus_toe": net[toe],
        "sigma_cloud_toe": cloud[toe].reshape(-1, 3),
        "sigma_cloud_midscale": cloud[~toe].reshape(-1, 3),
        "random_uniform": random_uniform,
        "random_near_neutral": random_near_neutral,
        "formed_frame_v49_common": formed_net,
        "formed_frame_independent_records": formed_independent_net,
    }

    # ---- solver equivalence: studio Numba kernel vs original engine solver ----
    equivalence_probe = np.concatenate([cloud[toe].reshape(-1, 3)[::7], random_uniform[:5000], formed_net[::40]])
    report["studio_vs_legacy_solver"] = error_summary(direct_printer_density(equivalence_probe), legacy_direct_printer_density(equivalence_probe))
    print("studio/legacy printer-density agreement:", report["studio_vs_legacy_solver"]["max_abs"], flush=True)

    # ---- direct authority and its own solver residual -----------------------
    started = time.perf_counter()
    direct = {name: direct_printer_density(values) for name, values in probes.items()}
    report["direct_evaluation_seconds"] = time.perf_counter() - started
    report["direct_solver_residual_status_m"] = {
        name: error_summary(direct_solve_residual(values) + np.maximum(values, 0.0), np.maximum(values, 0.0))
        for name, values in probes.items()
        if name in {"neutral_locus", "sigma_cloud_toe", "sigma_cloud_midscale", "formed_frame_v49_common"}
    }

    # ---- V86 reproduction: runtime 29 cube ----------------------------------
    runtime_errors = {name: error_summary(runtime_29_cube(values), direct[name]) for name, values in probes.items()}
    report["runtime_29_cube_uniform"] = runtime_errors
    neutral_signed = (runtime_29_cube(net) - direct["neutral_locus"]).astype(np.float64)
    worst_neutral = int(np.argmax(np.abs(neutral_signed).max(axis=1)))
    report["runtime_29_cube_neutral_worst"] = {
        "log_exposure": float(log_exposure[worst_neutral]),
        "signed_error_rgb": [float(v) for v in neutral_signed[worst_neutral]],
        "error_at_minus_3_logE_rgb": [float(v) for v in neutral_signed[int(np.argmin(np.abs(log_exposure + 3.0)))]],
    }

    # ---- candidate lattices --------------------------------------------------
    candidates = []
    for size in (29, 57, 113):
        candidates.append(("uniform", size, 1.0))
    for size in (33, 65, 129):
        candidates.append(("power2", size, 2.0))
    for size in (65, 129):
        candidates.append(("power1.5", size, 1.5))
    candidates = [c for c in candidates if c[1] <= args.largest]
    lattice_results = {}
    chosen = None
    for family, size, power in candidates:
        axis = uniform_axis(size, e.NEGATIVE_5279_MAX_RECORD_DENSITY) if power == 1.0 else power_axis(size, e.NEGATIVE_5279_MAX_RECORD_DENSITY, power)
        lattice = Lattice(f"{family}_{size}", axis, direct_printer_density)
        errors = {name: error_summary(lattice.sample(values), direct[name]) for name, values in probes.items()}
        worst = max(v["max_abs"] for v in errors.values())
        passes = worst < GATE_DENSITY
        lattice_results[lattice.name] = {
            "family": family,
            "size": size,
            "axis_power": power,
            "cells": size ** 3,
            "build_seconds": lattice.build_seconds,
            "worst_max_abs": worst,
            "passes_gate": passes,
            "errors": errors,
        }
        print(f"{lattice.name:>12}: worst {worst:.6f} D  build {lattice.build_seconds:.1f}s  pass={passes}", flush=True)
        if passes and (chosen is None or size ** 3 < chosen[1].size ** 3):
            chosen = (lattice.name, lattice)
    report["printer_density_lattices"] = lattice_results
    report["chosen_printer_lattice"] = chosen[0] if chosen else None

    # ---- 2383 projection lattice audit --------------------------------------
    print_axis = np.linspace(0.0, e.PRINT_2383_DMAX, 2049)
    print_probe_neutral = np.repeat(print_axis[:, None], 3, axis=1)
    print_probe_random = rng.uniform(0.0, e.PRINT_2383_DMAX, size=(args.random_samples, 3))
    # Real print densities of the formed frame through the direct printer authority.
    printer_formed = direct["formed_frame_v49_common"] + 0.0
    negative_printer = (printer_formed + np.minimum(negative["formed_common"].reshape(-1, 3) - e.SENSITO_DMIN_RGB, 0.0)).astype(np.float32)
    print_formed = e.print_2383_density_from_negative(negative_printer.reshape(1, -1, 3)).reshape(-1, 3).astype(np.float64)
    print_probes = {
        "print_neutral_axis": print_probe_neutral,
        "print_random_uniform": print_probe_random,
        "print_formed_frame": print_formed,
    }
    direct_projection = {name: direct_projection_rgb(values) for name, values in print_probes.items()}
    projection_results = {}
    for size in (25, 65, 129, 257):
        lattice = Lattice(f"projection_uniform_{size}", uniform_axis(size, e.PRINT_2383_DMAX), direct_projection_rgb)
        per_probe = {}
        for name, values in print_probes.items():
            sampled = lattice.sample(values).astype(np.float64)
            reference = direct_projection[name]
            relative = np.abs(sampled - reference) / np.maximum(np.abs(reference), 1e-4)
            lab_delta = np.linalg.norm(oklab(np.clip(sampled, 0, 4)) - oklab(np.clip(reference, 0, 4)), axis=-1)
            per_probe[name] = {
                "max_abs_linear": float(np.abs(sampled - reference).max()),
                "max_relative_linear": float(relative.max()),
                "p99_relative_linear": float(np.percentile(relative, 99.0)),
                "max_oklab_distance": float(lab_delta.max()),
                "p99_oklab_distance": float(np.percentile(lab_delta, 99.0)),
            }
        projection_results[lattice.name] = {
            "size": size,
            "cells": size ** 3,
            "build_seconds": lattice.build_seconds,
            "errors": per_probe,
        }
        print(f"{lattice.name:>24}: max rel {max(v['max_relative_linear'] for v in per_probe.values()):.5f}", flush=True)
    report["projection_lattices"] = projection_results

    # ---- display consequence: runtime vs direct authority -------------------
    toe_log_exposure = np.array([-3.5, -3.25, -3.0, -2.75, -2.5, -2.25, -2.0, -1.5, -1.0, -0.5])
    toe_net, toe_sigma = neutral_locus(toe_log_exposure)
    toe_cloud = perturbation_cloud(toe_net, toe_sigma) + e.SENSITO_DMIN_RGB  # total density
    toe_cloud = toe_cloud.reshape(1, -1, 3).astype(np.float32)
    frame_common = negative["formed_common"].astype(np.float32)
    frame_mean = negative["mean"].astype(np.float32)

    authorities = {"runtime_29_cube": runtime_29_cube, "direct": direct_printer_density}
    if chosen is not None:
        chosen_lattice = chosen[1]
        authorities[f"lattice_{chosen[0]}"] = lambda net, _l=chosen_lattice: _l.sample(net)
    display = {}
    for name, function in authorities.items():
        install_printer_density(function)
        started = time.perf_counter()
        display[name] = {
            "toe_cloud": observe(toe_cloud),
            "frame_common": observe(frame_common),
            "frame_mean": observe(frame_mean),
            "neutral_mid_scanner_density": [float(v) for v in e.NEUTRAL_MID_SCANNER_DENSITY],
            "seconds": time.perf_counter() - started,
        }
        print(f"observer graph under {name}: {display[name]['seconds']:.1f}s", flush=True)
    install_printer_density(ORIGINAL_RUNTIME)

    consequence: dict[str, object] = {}
    reference = display["direct"]
    for name in authorities:
        if name == "direct":
            continue
        entry: dict[str, object] = {}
        for observer in ("projection", "scan"):
            cand = display[name]["toe_cloud"][observer][0].reshape(len(toe_log_exposure), 27, 3)
            ref = reference["toe_cloud"][observer][0].reshape(len(toe_log_exposure), 27, 3)
            per_exposure = []
            for i, le in enumerate(toe_log_exposure):
                cand_lab = oklab(cand[i])
                ref_lab = oklab(ref[i])
                mean_delta = cand_lab.mean(axis=0) - ref_lab.mean(axis=0)
                per_pixel = np.linalg.norm(cand_lab - ref_lab, axis=-1)
                per_exposure.append(
                    {
                        "log_exposure": float(le),
                        "display_luma_direct": float(np.einsum("nc,c->n", ref[i], [0.2126, 0.7152, 0.0722]).mean()),
                        "mean_oklab_delta_Lab": [float(v) for v in mean_delta],
                        "mean_delta_chroma_direction_deg": hue_degrees(mean_delta[1:3]),
                        "mean_delta_chroma_magnitude": float(np.linalg.norm(mean_delta[1:3])),
                        "max_pixel_oklab_distance": float(per_pixel.max()),
                        "neutral_point_oklab_delta_Lab": [float(v) for v in (cand_lab[13] - ref_lab[13])],
                    }
                )
            frame_cand = oklab(display[name]["frame_common"][observer])
            frame_ref = oklab(reference["frame_common"][observer])
            luma = np.einsum("hwc,c->hw", reference["frame_common"][observer], [0.2126, 0.7152, 0.0722])
            shadows = luma < np.percentile(luma, 25)
            frame_delta = frame_cand - frame_ref
            shadow_mean = frame_delta[shadows].mean(axis=0)
            entry[observer] = {
                "toe_cloud": per_exposure,
                "formed_frame_shadow_quartile_mean_oklab_delta_Lab": [float(v) for v in shadow_mean],
                "formed_frame_shadow_quartile_delta_direction_deg": hue_degrees(shadow_mean[1:3]),
                "formed_frame_shadow_quartile_delta_chroma": float(np.linalg.norm(shadow_mean[1:3])),
                "formed_frame_max_pixel_oklab_distance": float(np.linalg.norm(frame_delta, axis=-1).max()),
                "formed_frame_p99_pixel_oklab_distance": float(np.percentile(np.linalg.norm(frame_delta, axis=-1), 99.0)),
                "formed_frame_mean_pixel_oklab_distance": float(np.linalg.norm(frame_delta, axis=-1).mean()),
            }
        consequence[name] = entry
    report["display_consequence_vs_direct"] = consequence

    # ---- gate decision --------------------------------------------------------
    report["gate"] = {
        "runtime_29_cube_worst_shadow_error": max(
            runtime_errors["sigma_cloud_toe"]["max_abs"], runtime_errors["neutral_locus_toe"]["max_abs"]
        ),
        "runtime_29_cube_worst_midscale_error": runtime_errors["sigma_cloud_midscale"]["max_abs"],
        "runtime_29_cube_passes": max(v["max_abs"] for v in runtime_errors.values()) < GATE_DENSITY,
        "chosen_lattice": chosen[0] if chosen else None,
        "chosen_lattice_worst_error": lattice_results[chosen[0]]["worst_max_abs"] if chosen else None,
        "chosen_lattice_passes": bool(chosen),
    }
    report["wall_seconds"] = time.perf_counter() - wall_started
    report["sources"] = {
        "emulsion_experiment_sha256": hashlib.sha256(Path(e.__file__).read_bytes()).hexdigest(),
        "audit_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (args.output / "audit.json").write_text(json.dumps(report, indent=2))
    if chosen is not None:
        np.save(args.output / f"printer_density_{chosen[0]}_axis.npy", chosen[1].axis.astype(np.float32))
    print(json.dumps(report["gate"], indent=2))
    print(f"wall {report['wall_seconds']:.1f}s -> {args.output / 'audit.json'}")


if __name__ == "__main__":
    main()
