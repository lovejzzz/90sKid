#!/usr/bin/env python3
"""Propagate Kodak's 5279 marginal RMS through legal covariance envelopes.

Kodak publishes three Status-M, 48 micrometre RMS curves, not their joint
covariance.  This audit keeps those three diagonal variances exact and asks
how much a local scan or print observer can vary over every positive
semidefinite 3x3 correlation matrix.  It is an observer-space uncertainty
envelope, not a fitted covariance and not a new image profile.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import differential_evolution

from audit_v79_projection_grain_policy_ownership import (
    LUMA,
    publish_policy,
    render_local_endpoint,
)
from emulsion5279 import legacy
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.pipeline import Emulsion5279Engine, FormedNegative


LOG_EXPOSURES = np.asarray(
    [-4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0],
    dtype=np.float64,
)
FINITE_RESPONSE_SCALES = (1.0, 0.5)
PATCH_SHAPE = (24, 24)


def correlation_from_angles(angles: np.ndarray) -> np.ndarray:
    """Rank-two boundary of the three-dimensional correlation elliptope."""
    directions = np.asarray([0.0, angles[0], angles[1]], dtype=np.float64)
    return np.cos(directions[:, None] - directions[None, :])


def optimize_elliptope_support(
    quadratic: np.ndarray,
    maximize: bool,
) -> tuple[float, np.ndarray, dict[str, object]]:
    """Optimize trace(QR) on the exact 3x3 correlation elliptope boundary."""
    q = np.asarray(quadratic, dtype=np.float64)

    def objective(angles: np.ndarray) -> float:
        value = float(np.sum(q * correlation_from_angles(angles)))
        return -value if maximize else value

    result = differential_evolution(
        objective,
        bounds=((0.0, 2.0 * math.pi), (0.0, 2.0 * math.pi)),
        seed=8605279,
        tol=1e-11,
        atol=1e-13,
        polish=True,
        updating="immediate",
        workers=1,
    )
    correlation = correlation_from_angles(result.x)
    variance = float(np.sum(q * correlation))
    eigenvalues = np.linalg.eigvalsh(correlation)
    return variance, correlation, {
        "optimizer_success": bool(result.success),
        "optimizer_message": str(result.message),
        "objective_evaluations": int(result.nfev),
        "correlation_diagonal_error": float(
            np.max(np.abs(np.diag(correlation) - 1.0))
        ),
        "minimum_correlation_eigenvalue": float(np.min(eigenvalues)),
        "rank_boundary_determinant": float(np.linalg.det(correlation)),
    }


def scalar_exact_std_bounds(weights: np.ndarray) -> tuple[float, float]:
    """Exact Gram-vector bounds for one scalar observer with fixed marginals."""
    lengths = np.abs(np.asarray(weights, dtype=np.float64))
    total = float(np.sum(lengths))
    minimum = max(2.0 * float(np.max(lengths)) - total, 0.0)
    return minimum, total


def metric_quadratics(one_sigma_response: np.ndarray) -> dict[str, np.ndarray]:
    transfer = np.asarray(one_sigma_response, dtype=np.float64)
    identity = np.eye(3, dtype=np.float64)
    opponent = identity - np.ones((3, 1), dtype=np.float64) @ LUMA[None, :]
    metrics: dict[str, np.ndarray] = {
        "rgb_rms": transfer.T @ transfer / 3.0,
        "luma_rms": transfer.T @ np.outer(LUMA, LUMA) @ transfer,
        "opponent_rms": transfer.T @ opponent.T @ opponent @ transfer / 3.0,
    }
    for channel, name in enumerate(("red_rms", "green_rms", "blue_rms")):
        selector = np.zeros(3, dtype=np.float64)
        selector[channel] = 1.0
        metrics[name] = transfer.T @ np.outer(selector, selector) @ transfer
    return metrics


def envelope(one_sigma_response: np.ndarray) -> dict[str, object]:
    rows: dict[str, object] = {}
    identity = np.eye(3, dtype=np.float64)
    common = np.ones((3, 3), dtype=np.float64)
    for name, quadratic in metric_quadratics(one_sigma_response).items():
        minimum_variance, minimum_correlation, minimum_audit = (
            optimize_elliptope_support(quadratic, False)
        )
        maximum_variance, maximum_correlation, maximum_audit = (
            optimize_elliptope_support(quadratic, True)
        )
        minimum_variance = max(minimum_variance, 0.0)
        maximum_variance = max(maximum_variance, 0.0)
        row: dict[str, object] = {
            "minimum_psd_outer_std": math.sqrt(minimum_variance),
            "independent_std": math.sqrt(max(float(np.sum(quadratic * identity)), 0.0)),
            "common_event_std": math.sqrt(max(float(np.sum(quadratic * common)), 0.0)),
            "maximum_psd_outer_std": math.sqrt(maximum_variance),
            "maximum_over_independent": math.sqrt(maximum_variance)
            / max(math.sqrt(max(float(np.sum(quadratic * identity)), 0.0)), 1e-30),
            "minimum_correlation": minimum_correlation.tolist(),
            "maximum_correlation": maximum_correlation.tolist(),
            "minimum_solver_audit": minimum_audit,
            "maximum_solver_audit": maximum_audit,
        }
        if name in {"red_rms", "green_rms", "blue_rms", "luma_rms"}:
            if name == "luma_rms":
                scalar_weights = LUMA @ np.asarray(one_sigma_response)
            else:
                scalar_weights = (
                    np.asarray(one_sigma_response)[
                        ("red_rms", "green_rms", "blue_rms").index(name)
                    ]
                )
            exact_minimum, exact_maximum = scalar_exact_std_bounds(scalar_weights)
            row["exact_scalar_std_bounds"] = [exact_minimum, exact_maximum]
            row["solver_maximum_absolute_closure_error"] = max(
                abs(row["minimum_psd_outer_std"] - exact_minimum),
                abs(row["maximum_psd_outer_std"] - exact_maximum),
            )
        rows[name] = row
    return rows


def observed_arrays(
    engine: Emulsion5279Engine,
    density: np.ndarray,
) -> dict[str, np.ndarray]:
    negative = FormedNegative(density, density)
    direct = render_local_endpoint(engine, negative, 0, 1.0, 1.0)
    managed = publish_policy(
        direct,
        {"publication": "scan_referenced", "publication_hf_retention": 0.0},
    )
    centre = (density.shape[0] // 2, density.shape[1] // 2)
    return {
        "direct_2383_projection": np.asarray(direct["projection"][centre]),
        "scan": np.asarray(direct["scan"][centre]),
        "current_v72_published_projection": np.asarray(
            managed["projection"][centre]
        ),
    }


def local_jacobians(
    engine: Emulsion5279Engine,
    base_density: np.ndarray,
    sigma: np.ndarray,
    response_scale: float,
) -> dict[str, np.ndarray]:
    base = np.broadcast_to(base_density, PATCH_SHAPE + (3,)).copy().astype(np.float32)
    columns: dict[str, list[np.ndarray]] = {
        "direct_2383_projection": [],
        "scan": [],
        "current_v72_published_projection": [],
    }
    for record in range(3):
        step = float(sigma[record]) * float(response_scale)
        plus = base.copy()
        minus = base.copy()
        plus[..., record] += step
        minus[..., record] -= step
        observed_plus = observed_arrays(engine, plus)
        observed_minus = observed_arrays(engine, minus)
        for branch in columns:
            columns[branch].append(
                (observed_plus[branch] - observed_minus[branch]) / (2.0 * step)
            )
    return {
        branch: np.stack(values, axis=1).astype(np.float64)
        for branch, values in columns.items()
    }


def exact_2383_printer_density_from_status_m(
    model,
    status_m_net_density: np.ndarray,
) -> np.ndarray:
    """Evaluate V61's joint spectral model without the 29-cube runtime LUT."""
    source = np.asarray(status_m_net_density, dtype=np.float64).reshape(-1, 3)
    cmy = model.solve_5279_analytical_cmy_from_status_m_net_density(source)
    spectra = np.asarray(
        model.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float64
    )
    lamp = np.asarray(
        model._blackbody_spd(model.NEGATIVE_DYE_WAVELENGTHS_NM, 3200.0),
        dtype=np.float64,
    )
    sensitivity = np.power(
        10.0,
        np.asarray(model.PRINT_2383_LOG_SENSITIVITY_CMY, dtype=np.float64),
    )
    weights = lamp[:, None] * sensitivity
    weights /= np.sum(weights, axis=0, keepdims=True)
    spectral_density = (
        np.asarray(model.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY, dtype=np.float64)[
            None, :
        ]
        + cmy @ spectra.T
    )
    transmission = np.power(10.0, -np.clip(spectral_density, 0.0, 16.0))
    return -np.log10(np.maximum(transmission @ weights, 1e-12))


def spectral_lut_precision_audit(
    model,
    total_density: np.ndarray,
    sigma: np.ndarray,
) -> dict[str, object]:
    net = np.maximum(
        np.asarray(total_density, dtype=np.float64)
        - np.asarray(model.SENSITO_DMIN_RGB, dtype=np.float64),
        0.0,
    )
    points = [net]
    labels = ["mean"]
    for record, name in enumerate(("red", "green", "blue")):
        for direction, suffix in ((-1.0, "minus_sigma"), (1.0, "plus_sigma")):
            point = net.copy()
            point[record] = max(point[record] + direction * sigma[record], 0.0)
            points.append(point)
            labels.append(f"{name}_{suffix}")
    points_array = np.asarray(points, dtype=np.float32)
    runtime = model.apply_5279_to_2383_printer_density_lut(points_array).astype(
        np.float64
    )
    exact = exact_2383_printer_density_from_status_m(model, points_array)
    error = runtime - exact
    maximum_index = np.unravel_index(np.argmax(np.abs(error)), error.shape)
    return {
        "status_m_net_density_rgb": net.tolist(),
        "points": [
            {
                "label": label,
                "status_m_net_density_rgb": point.tolist(),
                "runtime_29_lut_printer_density_rgb": approximate.tolist(),
                "direct_joint_spectral_printer_density_rgb": reference.tolist(),
                "runtime_minus_direct_rgb": delta.tolist(),
            }
            for label, point, approximate, reference, delta in zip(
                labels, points_array, runtime, exact, error, strict=True
            )
        ],
        "rms_printer_density_error": float(np.sqrt(np.mean(np.square(error)))),
        "maximum_absolute_printer_density_error": float(np.max(np.abs(error))),
        "maximum_error_point": labels[int(maximum_index[0])],
        "maximum_error_output_record": ("red", "green", "blue")[
            int(maximum_index[1])
        ],
        "maximum_signed_printer_density_error": float(error[maximum_index]),
        "mean_runtime_minus_direct_rgb": error[0].tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    config = EngineConfig(
        profile="v72",
        mode=EngineMode.REFERENCE,
        research_baseline=True,
        opencv_threads=1,
        binomial_workers=1,
        numba_threads=1,
        array_workers=1,
        observer_branch_workers=1,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    model = legacy.model

    if engine.profile.PROFILE.get("projection_colour_policy") != "scan_referenced_v31":
        raise RuntimeError("V86 expected V72's declared scan-referenced publication")
    if engine.profile.PROFILE.get("final_adapter_opponent_high_frequency_retention") != 0.0:
        raise RuntimeError("V86 expected V72's zero-retention publication adapter")

    rows: list[dict[str, object]] = []
    maximum_response_scale_relative_delta = 0.0
    maximum_scalar_solver_closure_error = 0.0
    maximum_spectral_lut_error = 0.0
    maximum_spectral_lut_error_location: dict[str, object] | None = None
    for log_exposure in LOG_EXPOSURES:
        exposure = np.full((1, 1, 3), log_exposure, dtype=np.float32)
        density = model.develop_5279_record_density_from_log_exposure(exposure)[0, 0]
        sigma = model.published_5279_granularity_sigma(exposure)[0, 0].astype(np.float64)
        lut_precision = spectral_lut_precision_audit(model, density, sigma)
        if lut_precision["maximum_absolute_printer_density_error"] > maximum_spectral_lut_error:
            maximum_spectral_lut_error = float(
                lut_precision["maximum_absolute_printer_density_error"]
            )
            maximum_spectral_lut_error_location = {
                "log_exposure": float(log_exposure),
                "maximum_absolute_printer_density_error": maximum_spectral_lut_error,
                "point": lut_precision["maximum_error_point"],
                "output_record": lut_precision["maximum_error_output_record"],
                "signed_printer_density_error": lut_precision[
                    "maximum_signed_printer_density_error"
                ],
            }
        jacobians_by_scale = {
            str(scale): local_jacobians(engine, density, sigma, scale)
            for scale in FINITE_RESPONSE_SCALES
        }
        selected = jacobians_by_scale[str(FINITE_RESPONSE_SCALES[0])]
        convergence: dict[str, dict[str, float]] = {}
        for branch in selected:
            full_sigma_response = selected[branch] @ np.diag(sigma)
            half_sigma_extrapolated = (
                jacobians_by_scale[str(FINITE_RESPONSE_SCALES[1])][branch]
                @ np.diag(sigma)
            )
            absolute = float(
                np.max(np.abs(full_sigma_response - half_sigma_extrapolated))
            )
            relative = absolute / max(
                float(np.max(np.abs(full_sigma_response))),
                float(np.max(np.abs(half_sigma_extrapolated))),
                1e-12,
            )
            convergence[branch] = {
                "maximum_absolute_jacobian_delta": absolute,
                "maximum_relative_jacobian_delta": relative,
            }
            maximum_response_scale_relative_delta = max(
                maximum_response_scale_relative_delta, relative
            )
        branch_rows: dict[str, object] = {}
        for branch, jacobian in selected.items():
            one_sigma_response = jacobian @ np.diag(sigma)
            branch_envelope = envelope(one_sigma_response)
            for metric in branch_envelope.values():
                maximum_scalar_solver_closure_error = max(
                    maximum_scalar_solver_closure_error,
                    float(metric.get("solver_maximum_absolute_closure_error", 0.0)),
                )
            branch_rows[branch] = {
                "one_sigma_secant_jacobian_linear_rec709_per_density": (
                    jacobian.tolist()
                ),
                "one_sigma_response_matrix_linear_rec709": (
                    one_sigma_response.tolist()
                ),
                "covariance_envelope": branch_envelope,
            }
        rows.append(
            {
                "log_exposure": float(log_exposure),
                "mean_status_m_record_density_rgb": density.tolist(),
                "published_48um_sigma_d_rgb": sigma.tolist(),
                "spectral_lut_precision": lut_precision,
                "one_vs_half_sigma_response_delta": convergence,
                "branches": branch_rows,
            }
        )

    report = {
        "audit": "V86 observer-space covariance envelope",
        "profile": engine.profile.PROFILE,
        "measurement_authority": {
            "stock": "Kodak VISION 500T Color Negative Film 5279",
            "quantity": "Status-M RMS diffuse density by record",
            "aperture_diameter_um": float(
                model.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
            ),
            "known": "three marginal variances at each published exposure",
            "unknown": (
                "cross-record covariance, cross-power spectra, joint tails and "
                "stock-specific finite-event law"
            ),
        },
        "method": {
            "observer_linearization": (
                "symmetric finite-amplitude secant of the deterministic local "
                "density mapping in linear Rec.709; both mean and formed "
                "density move, and each record's step equals its own published "
                "one-sigma density RMS"
            ),
            "finite_response_scales_sigma": list(FINITE_RESPONSE_SCALES),
            "covariance_domain": (
                "all positive-semidefinite 3x3 correlation matrices with unit "
                "diagonal; this is a mathematical outer envelope"
            ),
            "elliptope_solution": (
                "linear support optimized on the exact rank-two boundary of the "
                "3x3 correlation elliptope; scalar rows also carry closed-form "
                "Gram-vector bounds"
            ),
            "not_modelled": (
                "frequency-dependent cross-spectrum, DIR event feasibility, "
                "non-Gaussian tails and spatial observer MTF"
            ),
        },
        "lattice_resolution_boundary": {
            "joint_status_m_to_spectral_printer_lut_size": int(
                model._NEGATIVE_5279_TO_2383_PRINTER_DENSITY_LUT.shape[0]
            ),
            "joint_status_m_lut_cell_width_density": float(
                model.NEGATIVE_5279_MAX_RECORD_DENSITY
                / (model._NEGATIVE_5279_TO_2383_PRINTER_DENSITY_LUT.shape[0] - 1)
            ),
            "complete_monitor_output_lut_size": int(
                model._PRINT_2383_MONITOR_OUTPUT_LUT.shape[0]
            ),
            "complete_monitor_output_lut_cell_width_density": float(
                (model.NEGATIVE_5279_MAX_RECORD_DENSITY - (-0.16))
                / (model._PRINT_2383_MONITOR_OUTPUT_LUT.shape[0] - 1)
            ),
            "interpretation": (
                "Both stages are continuous trilinear interpolation, not code-value "
                "quantization. The 193 cube cannot recover curvature already "
                "approximated by the upstream 29-cube joint spectral inversion."
            ),
        },
        "audit_closure": {
            "maximum_one_vs_half_sigma_response_relative_delta": (
                maximum_response_scale_relative_delta
            ),
            "maximum_scalar_solver_absolute_std_error": (
                maximum_scalar_solver_closure_error
            ),
            "maximum_29_lut_vs_direct_spectral_printer_density_error": (
                maximum_spectral_lut_error
            ),
            "maximum_29_lut_error_location": maximum_spectral_lut_error_location,
        },
        "exposure_rows": rows,
        "decision": {
            "image_profile_change": False,
            "reason": (
                "The covariance envelope cannot identify which legal covariance "
                "belongs to 5279. Separately, the shadow spectral-LUT error is "
                "large enough to justify a new precision implementation, but that "
                "implementation must pass a direct-spectral equivalence gate before "
                "it can change released pixels."
            ),
            "next_gate": (
                "Replace or densify the 29-cube Status-M-to-spectral-printer stage, "
                "rebuild both observers from the same direct authority, and prove "
                "shadow error falls below 0.001 D without changing the midscale by "
                "more than the same tolerance. Only then return to the V81/V82/V83 "
                "finite-event covariance gate."
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["audit_closure"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
