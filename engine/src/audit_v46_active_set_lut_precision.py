#!/usr/bin/env python3
"""Audit interpolated fixed-active-set cubes against the exact V46 NNLS."""

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


def trilinear_axis(
    lut: np.ndarray, source: np.ndarray, axis: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    points = np.asarray(source, dtype=np.float64).reshape(-1, 3)
    coordinates = np.asarray(axis, dtype=np.float64)
    clipped = np.clip(points, coordinates[0], coordinates[-1])
    lower = np.searchsorted(coordinates, clipped, side="right") - 1
    lower = np.clip(lower, 0, coordinates.size - 2).astype(np.int16)
    upper = lower + 1
    lower_value = coordinates[lower]
    upper_value = coordinates[upper]
    fraction = (clipped - lower_value) / np.maximum(
        upper_value - lower_value, 1e-30
    )
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


def _lagrange4_weights(axis: np.ndarray, values: np.ndarray):
    lower = np.searchsorted(axis, values, side="right") - 1
    base = np.clip(lower - 1, 0, axis.size - 4).astype(np.int16)
    indices = base[:, None] + np.arange(4, dtype=np.int16)[None, :]
    nodes = axis[indices]
    weights = np.ones_like(nodes, dtype=np.float64)
    for column in range(4):
        for other in range(4):
            if column == other:
                continue
            weights[:, column] *= (values - nodes[:, other]) / (
                nodes[:, column] - nodes[:, other]
            )
    return indices, weights, lower.astype(np.int16)


def tricubic_axis(
    lut: np.ndarray, source: np.ndarray, axis: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    points = np.asarray(source, dtype=np.float64).reshape(-1, 3)
    clipped = np.clip(points, axis[0], axis[-1])
    ci, cw, cl = _lagrange4_weights(axis, clipped[:, 0])
    mi, mw, ml = _lagrange4_weights(axis, clipped[:, 1])
    yi, yw, yl = _lagrange4_weights(axis, clipped[:, 2])
    result = np.zeros((points.shape[0], lut.shape[-1]), dtype=np.float64)
    for red in range(4):
        for green in range(4):
            for blue in range(4):
                weight = cw[:, red] * mw[:, green] * yw[:, blue]
                result += (
                    lut[ci[:, red], mi[:, green], yi[:, blue]]
                    * weight[:, None]
                )
    return result, np.stack([cl, ml, yl], axis=1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("printer", type=Path)
    parser.add_argument("residual", type=Path)
    parser.add_argument("--axis", type=Path)
    parser.add_argument(
        "--interpolation", choices=("linear", "cubic"), default="linear"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    v72_profile.apply(e)
    printer = np.load(args.printer, mmap_mode="r")
    residual = np.load(args.residual, mmap_mode="r")
    if printer.shape[:4] != residual.shape or printer.shape[0] != 8:
        raise ValueError("expected eight matching active-set cubes")
    axis = (
        np.load(args.axis).astype(np.float64)
        if args.axis is not None
        else np.linspace(
            0.0,
            e.NEGATIVE_5279_MAX_RECORD_DENSITY,
            printer.shape[1],
            dtype=np.float64,
        )
    )
    if axis.shape != (printer.shape[1],) or np.any(np.diff(axis) <= 0.0):
        raise ValueError("axis must be strictly increasing and match the cubes")

    points = audit_points()
    sampler = trilinear_axis if args.interpolation == "linear" else tricubic_axis
    best_residual = np.full(points.shape[0], np.inf, dtype=np.float64)
    best_printer = np.empty_like(points, dtype=np.float64)
    approximate_mask = np.zeros(points.shape[0], dtype=np.uint8)
    branch_printers = np.empty((8, points.shape[0], 3), dtype=np.float64)
    point_lower = None
    interpolation_started = time.perf_counter()
    for mask in range(8):
        branch_residual, lower = sampler(
            residual[mask][..., None], points, axis
        )
        if point_lower is None:
            point_lower = lower
        branch_printer, _ = sampler(printer[mask], points, axis)
        branch_printers[mask] = branch_printer
        improved = branch_residual[:, 0] < best_residual
        best_residual[improved] = branch_residual[improved, 0]
        best_printer[improved] = branch_printer[improved]
        approximate_mask[improved] = mask
    interpolation_seconds = time.perf_counter() - interpolation_started

    exact_started = time.perf_counter()
    exact_cmy, exact_mask, exact_residual = solve_nnls(e, points)
    exact_printer = printer_density_from_cmy(e, exact_cmy).astype(np.float64)
    exact_seconds = time.perf_counter() - exact_started
    oracle_printer = branch_printers[exact_mask, np.arange(points.shape[0])]
    oracle_error = oracle_printer - exact_printer
    oracle_absolute = np.abs(oracle_error)
    oracle_worst = np.unravel_index(
        np.argmax(oracle_absolute), oracle_absolute.shape
    )
    error = best_printer - exact_printer
    absolute = np.abs(error)
    node_mask = np.argmin(np.asarray(residual), axis=0).astype(np.uint8)
    risk = np.zeros(
        (node_mask.shape[0] - 1, node_mask.shape[1] - 1, node_mask.shape[2] - 1),
        dtype=bool,
    )
    first_corner = node_mask[:-1, :-1, :-1]
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                risk |= (
                    node_mask[
                        red : red + risk.shape[0],
                        green : green + risk.shape[1],
                        blue : blue + risk.shape[2],
                    ]
                    != first_corner
                )
    assert point_lower is not None
    lower_for_risk = np.minimum(point_lower, np.asarray(risk.shape) - 1)
    flagged = risk[
        lower_for_risk[:, 0], lower_for_risk[:, 1], lower_for_risk[:, 2]
    ]
    point_maximum_error = np.max(absolute, axis=1)
    estimator_rows = []
    if args.interpolation == "cubic":
        linear_residual = np.full(points.shape[0], np.inf, dtype=np.float64)
        linear_printer = np.empty_like(points, dtype=np.float64)
        for mask in range(8):
            branch_residual, _ = trilinear_axis(
                residual[mask][..., None], points, axis
            )
            branch_printer, _ = trilinear_axis(printer[mask], points, axis)
            improved = branch_residual[:, 0] < linear_residual
            linear_residual[improved] = branch_residual[improved, 0]
            linear_printer[improved] = branch_printer[improved]
        disagreement = np.max(np.abs(best_printer - linear_printer), axis=1)
        for threshold in (0.0001, 0.00025, 0.0005, 0.001):
            estimated = flagged | (disagreement >= threshold)
            estimator_rows.append(
                {
                    "linear_cubic_threshold": threshold,
                    "flagged_point_fraction": float(np.mean(estimated)),
                    "maximum_error_unflagged": float(
                        np.max(point_maximum_error[~estimated])
                    ),
                    "fraction_over_gate_unflagged": float(
                        np.mean(point_maximum_error[~estimated] >= 0.001)
                    ),
                }
            )
    worst = np.unravel_index(np.argmax(absolute), absolute.shape)
    report = {
        "policy": "trilinear_each_fixed_active_set_then_minimum_residual",
        "interpolation": args.interpolation,
        "lut_size": int(printer.shape[1]),
        "axis_first_steps": np.diff(axis[:5]).tolist(),
        "axis_last_steps": np.diff(axis[-5:]).tolist(),
        "point_count": int(points.shape[0]),
        "interpolation_seconds": interpolation_seconds,
        "exact_nnls_seconds": exact_seconds,
        "active_set_classification_accuracy": float(
            np.mean(approximate_mask == exact_mask)
        ),
        "active_set_boundary_risk": {
            "risk_cell_fraction": float(np.mean(risk)),
            "flagged_point_fraction": float(np.mean(flagged)),
            "maximum_error_flagged": float(np.max(point_maximum_error[flagged])),
            "maximum_error_unflagged": float(
                np.max(point_maximum_error[~flagged])
            ),
            "fraction_over_gate_flagged": float(
                np.mean(point_maximum_error[flagged] >= 0.001)
            ),
            "fraction_over_gate_unflagged": float(
                np.mean(point_maximum_error[~flagged] >= 0.001)
            ),
        },
        "adaptive_error_estimator_sweep": estimator_rows,
        "oracle_exact_mask_interpolation": {
            "maximum_absolute_printer_density_error": float(
                np.max(oracle_absolute)
            ),
            "p99_absolute_printer_density_error": float(
                np.percentile(oracle_absolute, 99)
            ),
            "rms_printer_density_error": float(
                np.sqrt(np.mean(np.square(oracle_error)))
            ),
            "worst_status_m_net_density": points[oracle_worst[0]].tolist(),
            "worst_output_record": ("red", "green", "blue")[
                oracle_worst[1]
            ],
            "worst_exact_mask": int(exact_mask[oracle_worst[0]]),
            "maximum_by_exact_mask": {
                str(mask): float(np.max(oracle_absolute[exact_mask == mask]))
                for mask in np.unique(exact_mask)
            },
        },
        "interpolated_residual_minus_exact": {
            "maximum_absolute": float(
                np.max(np.abs(best_residual - exact_residual))
            ),
            "rms": float(
                np.sqrt(np.mean(np.square(best_residual - exact_residual)))
            ),
        },
        "maximum_absolute_printer_density_error": float(absolute[worst]),
        "p99_absolute_printer_density_error": float(np.percentile(absolute, 99)),
        "rms_printer_density_error": float(np.sqrt(np.mean(np.square(error)))),
        "worst_status_m_net_density": points[worst[0]].tolist(),
        "worst_output_record": ("red", "green", "blue")[worst[1]],
        "worst_approximate_mask": int(approximate_mask[worst[0]]),
        "worst_exact_mask": int(exact_mask[worst[0]]),
        "quality_gate_maximum_density_error": 0.001,
        "quality_gate_pass": bool(float(absolute[worst]) < 0.001),
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
