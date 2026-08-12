#!/usr/bin/env python3
"""Compare the legacy clipped Newton inverse with V46 active-set NNLS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

import emulsion_experiment as e
import v72_profile
from audit_printer_density_hybrid_precision import audit_points
from v46_status_m_active_set import printer_density_from_cmy, solve_nnls


def residual_squared(target: np.ndarray, cmy: np.ndarray) -> np.ndarray:
    reconstructed = e.negative_5279_status_m_net_density_from_analytical_cmy(cmy)
    return np.sum(np.square(reconstructed.astype(np.float64) - target), axis=-1)


def summary(values: np.ndarray) -> dict[str, float]:
    source = np.asarray(values, dtype=np.float64)
    return {
        "maximum": float(np.max(source)),
        "p99": float(np.percentile(source, 99)),
        "median": float(np.median(source)),
        "mean": float(np.mean(source)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    v72_profile.apply(e)
    points = audit_points().astype(np.float64)

    started = time.perf_counter()
    legacy_cmy = e.solve_5279_analytical_cmy_from_status_m_net_density(points)
    legacy_seconds = time.perf_counter() - started
    legacy_error = residual_squared(points, legacy_cmy)
    legacy_printer = printer_density_from_cmy(e, legacy_cmy).astype(np.float64)

    started = time.perf_counter()
    nnls_cmy, active_masks, nnls_error = solve_nnls(e, points)
    nnls_seconds = time.perf_counter() - started
    nnls_printer = printer_density_from_cmy(e, nnls_cmy).astype(np.float64)
    printer_delta = nnls_printer - legacy_printer
    absolute_printer_delta = np.abs(printer_delta)
    worst = np.unravel_index(
        np.argmax(absolute_printer_delta), absolute_printer_delta.shape
    )

    rng = np.random.default_rng(46)
    reachable_cmy = rng.uniform(0.0, 3.0, size=(512, 3)).astype(np.float32)
    reachable_density = e.negative_5279_status_m_net_density_from_analytical_cmy(
        reachable_cmy
    )
    recovered_cmy, recovered_masks, recovered_error = solve_nnls(
        e, reachable_density
    )
    recovered_density = e.negative_5279_status_m_net_density_from_analytical_cmy(
        recovered_cmy
    )

    report = {
        "audit": "V46 Status-M nonnegative inverse",
        "point_count": int(points.shape[0]),
        "legacy_policy": "unconstrained_3x3_step_then_clip",
        "v46_policy": "enumerate_eight_active_sets_and_select_minimum_residual",
        "legacy_seconds": legacy_seconds,
        "v46_exact_seconds": nnls_seconds,
        "legacy_status_m_squared_residual": summary(legacy_error),
        "v46_status_m_squared_residual": summary(nnls_error),
        "v46_strictly_improves_fraction": float(
            np.mean(nnls_error < legacy_error - 1e-12)
        ),
        "v46_worsens_count": int(np.count_nonzero(nnls_error > legacy_error + 1e-12)),
        "active_mask_counts": {
            str(int(mask)): int(count)
            for mask, count in zip(
                *np.unique(active_masks, return_counts=True), strict=True
            )
        },
        "nnls_minus_legacy_printer_density": {
            "maximum_absolute": float(absolute_printer_delta[worst]),
            "p99_absolute": float(np.percentile(absolute_printer_delta, 99)),
            "rms": float(np.sqrt(np.mean(np.square(printer_delta)))),
            "worst_status_m_net_density": points[worst[0]].tolist(),
            "worst_output_record": ("red", "green", "blue")[worst[1]],
            "worst_signed_delta": float(printer_delta[worst]),
        },
        "reachable_closure": {
            "sample_count": int(reachable_cmy.shape[0]),
            "maximum_status_m_absolute_error": float(
                np.max(np.abs(recovered_density - reachable_density))
            ),
            "cmy_rms_error": float(
                np.sqrt(np.mean(np.square(recovered_cmy - reachable_cmy)))
            ),
            "maximum_squared_residual": float(np.max(recovered_error)),
            "all_full_active_set": bool(np.all(recovered_masks == 7)),
        },
        "interpretation": (
            "V46 changes the inverse only where the legacy clipped Newton step "
            "fails the conditional optimum on a nonnegative CMY boundary. "
            "Reachable mixtures close back to their source to floating precision."
        ),
    }
    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
