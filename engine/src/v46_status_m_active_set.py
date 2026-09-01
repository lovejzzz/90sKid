"""V46 nonnegative active-set inverse for Kodak 5279 Status-M density.

The legacy projected Gauss-Newton iteration takes a full unconstrained step and
clips negative CMY coefficients afterwards.  At a nonnegative boundary that
can leave the remaining free coefficients away from their conditional least-
squares optimum.  With only three dye coefficients the exact constrained
problem is small enough to enumerate all eight active sets explicitly.
"""

from __future__ import annotations

import numpy as np


def _status_m_context(model) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    weights = model._negative_5279_status_m_weights().astype(np.float64)
    dmin, spectra = model._negative_5279_status_m_model_spectra()
    dmin = dmin.astype(np.float64)
    spectra = spectra.astype(np.float64)
    with np.errstate(all="ignore"):
        base = -np.log10(
            np.maximum(np.power(10.0, -dmin) @ weights, 1e-30)
        )
    return weights, dmin, spectra, base


def _forward_and_jacobian(
    coefficients: np.ndarray,
    weights: np.ndarray,
    dmin: np.ndarray,
    spectra: np.ndarray,
    base: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    with np.errstate(all="ignore"):
        spectral_density = dmin[None, :] + coefficients @ spectra.T
        transmission = np.power(10.0, -spectral_density)
        integrated = np.maximum(transmission @ weights, 1e-30)
        density = -np.log10(integrated) - base
        jacobian = np.einsum(
            "nl,lj,lk->njk", transmission, weights, spectra
        ) / integrated[:, :, None]
    return density, jacobian


def solve_active_set(
    model,
    target_density: np.ndarray,
    mask: int,
    iterations: int = 24,
) -> tuple[np.ndarray, np.ndarray]:
    """Solve one fixed CMY active set and return coefficients plus squared error."""
    target = np.maximum(
        np.asarray(target_density, dtype=np.float64).reshape(-1, 3), 0.0
    )
    active = np.asarray([(mask >> channel) & 1 for channel in range(3)], bool)
    active_indices = np.flatnonzero(active)
    coefficients = np.zeros((target.shape[0], 3), dtype=np.float64)
    weights, dmin, spectra, base = _status_m_context(model)
    if active_indices.size:
        _, origin_jacobian = _forward_and_jacobian(
            np.zeros((1, 3), dtype=np.float64),
            weights,
            dmin,
            spectra,
            base,
        )
        linear = origin_jacobian[0][:, active_indices]
        with np.errstate(all="ignore"):
            coefficients[:, active_indices] = np.maximum(
                target @ np.linalg.pinv(linear).T, 0.0
            )
        diagonal = np.arange(active_indices.size)
        for _ in range(iterations):
            density, jacobian = _forward_and_jacobian(
                coefficients, weights, dmin, spectra, base
            )
            selected = jacobian[:, :, active_indices]
            residual = density - target
            normal = np.einsum("nji,njk->nik", selected, selected)
            normal[:, diagonal, diagonal] += 1e-8
            gradient = np.einsum("nji,nj->ni", selected, residual)
            with np.errstate(all="ignore"):
                step = -np.linalg.solve(normal, gradient[..., None])[..., 0]
            damping = np.maximum(
                1.0, np.max(np.abs(step), axis=1, keepdims=True) / 0.5
            )
            coefficients[:, active_indices] = np.clip(
                coefficients[:, active_indices] + step / damping,
                0.0,
                12.0,
            )
    density, _ = _forward_and_jacobian(
        coefficients, weights, dmin, spectra, base
    )
    squared_error = np.sum(np.square(density - target), axis=1)
    if not np.isfinite(coefficients).all() or not np.isfinite(squared_error).all():
        raise FloatingPointError("active-set Status-M solve produced non-finite data")
    return coefficients, squared_error


def solve_nnls(
    model,
    target_density: np.ndarray,
    iterations: int = 24,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Enumerate all CMY active sets and choose the minimum-residual legal solution."""
    source = np.asarray(target_density, dtype=np.float64)
    original_shape = source.shape
    flat = source.reshape(-1, 3)
    best_coefficients = np.zeros_like(flat)
    best_error = np.full(flat.shape[0], np.inf, dtype=np.float64)
    best_mask = np.zeros(flat.shape[0], dtype=np.uint8)
    for mask in range(8):
        coefficients, error = solve_active_set(
            model, flat, mask, iterations=iterations
        )
        better = error < best_error
        best_coefficients[better] = coefficients[better]
        best_error[better] = error[better]
        best_mask[better] = mask
    return (
        best_coefficients.reshape(original_shape).astype(np.float32),
        best_mask.reshape(original_shape[:-1]),
        best_error.reshape(original_shape[:-1]),
    )


def solve_nnls_allowed_masks(
    model,
    target_density: np.ndarray,
    allowed_masks: np.ndarray,
    iterations: int = 6,
    kkt_tolerance: float = 2e-7,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int | float]]:
    """Solve local candidate masks, then repair every failed KKT certificate.

    ``allowed_masks`` is N x 8 and normally comes from the eight corners of an
    adaptive parent cell.  A negative gradient in an inactive dye direction
    proves that the restricted solution is not NNLS-optimal; those points are
    re-solved with all eight active sets.  The acceleration is therefore
    certified per point rather than relying on branch continuity as a guess.
    """
    source = np.asarray(target_density, dtype=np.float64)
    original_shape = source.shape
    flat = np.maximum(source.reshape(-1, 3), 0.0)
    allowed = np.asarray(allowed_masks, dtype=bool)
    if allowed.shape != (flat.shape[0], 8):
        raise ValueError("allowed_masks must have shape (point_count, 8)")
    if np.any(~np.any(allowed, axis=1)):
        raise ValueError("every point must allow at least one active set")
    best_coefficients = np.zeros_like(flat)
    best_error = np.full(flat.shape[0], np.inf, dtype=np.float64)
    best_mask = np.zeros(flat.shape[0], dtype=np.uint8)
    branch_point_solves = 0
    for mask in range(8):
        indices = np.flatnonzero(allowed[:, mask])
        if not indices.size:
            continue
        coefficients, error = solve_active_set(
            model, flat[indices], mask, iterations=iterations
        )
        branch_point_solves += int(indices.size)
        improved = error < best_error[indices]
        selected = indices[improved]
        best_coefficients[selected] = coefficients[improved]
        best_error[selected] = error[improved]
        best_mask[selected] = mask

    weights, dmin, spectra, base = _status_m_context(model)
    density, jacobian = _forward_and_jacobian(
        best_coefficients, weights, dmin, spectra, base
    )
    gradient = np.einsum("nji,nj->ni", jacobian, density - flat)
    at_lower = best_coefficients <= 1e-7
    at_upper = best_coefficients >= 12.0 - 1e-7
    lower_failure = at_lower & (gradient < -float(kkt_tolerance))
    upper_failure = at_upper & (gradient > float(kkt_tolerance))
    fallback = np.any(lower_failure | upper_failure, axis=1)
    fallback_indices = np.flatnonzero(fallback)
    if fallback_indices.size:
        coefficients, masks, errors = solve_nnls(
            model, flat[fallback_indices], iterations=iterations
        )
        best_coefficients[fallback_indices] = coefficients
        best_mask[fallback_indices] = masks
        best_error[fallback_indices] = errors
    audit = {
        "point_count": int(flat.shape[0]),
        "restricted_branch_point_solves": branch_point_solves,
        "mean_restricted_masks_per_point": (
            float(branch_point_solves) / max(float(flat.shape[0]), 1.0)
        ),
        "kkt_fallback_point_count": int(fallback_indices.size),
        "kkt_fallback_fraction": float(
            fallback_indices.size / max(flat.shape[0], 1)
        ),
    }
    return (
        best_coefficients.reshape(original_shape).astype(np.float32),
        best_mask.reshape(original_shape[:-1]),
        best_error.reshape(original_shape[:-1]),
        audit,
    )


def printer_density_from_cmy(model, cmy: np.ndarray) -> np.ndarray:
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
    with np.errstate(all="ignore"):
        spectral_density = (
            np.asarray(
                model.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY, dtype=np.float64
            )[None, :]
            + np.asarray(cmy, dtype=np.float64).reshape(-1, 3) @ spectra.T
        )
        transmission = np.power(10.0, -np.clip(spectral_density, 0.0, 16.0))
        density = -np.log10(np.maximum(transmission @ weights, 1e-12))
    return density.reshape(np.asarray(cmy).shape).astype(np.float32)
