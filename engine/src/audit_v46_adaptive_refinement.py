#!/usr/bin/env python3
"""Prototype 4x local refinement only where the V46 base atlas is risky."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

import emulsion_experiment as e
import v72_profile
from audit_printer_density_hybrid_precision import audit_points
from audit_v46_active_set_lut_precision import trilinear_axis, tricubic_axis
from v46_status_m_active_set import (
    printer_density_from_cmy,
    solve_nnls,
    solve_nnls_allowed_masks,
)


def combined_atlas(printer, residual):
    mask = np.argmin(residual, axis=0).astype(np.uint8)
    combined = np.take_along_axis(
        np.asarray(printer), mask[None, ..., None], axis=0
    )[0]
    return combined, mask


def risk_cells(mask):
    shape = tuple(value - 1 for value in mask.shape)
    risk = np.zeros(shape, dtype=bool)
    first = mask[:-1, :-1, :-1]
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                risk |= mask[
                    red : red + shape[0],
                    green : green + shape[1],
                    blue : blue + shape[2],
                ] != first
    return risk


def solve_printer_batched(
    points, iterations, allowed_masks=None, chunk=20_000
):
    result = np.empty_like(points, dtype=np.float32)
    masks = np.empty(points.shape[0], dtype=np.uint8)
    restricted_audits = []
    for start in range(0, points.shape[0], chunk):
        stop = min(start + chunk, points.shape[0])
        if allowed_masks is None:
            cmy, mask, _ = solve_nnls(
                e, points[start:stop], iterations=iterations
            )
        else:
            cmy, mask, _, audit = solve_nnls_allowed_masks(
                e,
                points[start:stop],
                allowed_masks[start:stop],
                iterations=iterations,
            )
            restricted_audits.append(audit)
        result[start:stop] = printer_density_from_cmy(e, cmy)
        masks[start:stop] = mask
    restricted = None
    if restricted_audits:
        point_count = sum(int(row["point_count"]) for row in restricted_audits)
        branch_solves = sum(
            int(row["restricted_branch_point_solves"])
            for row in restricted_audits
        )
        fallback = sum(
            int(row["kkt_fallback_point_count"])
            for row in restricted_audits
        )
        restricted = {
            "point_count": point_count,
            "restricted_branch_point_solves": branch_solves,
            "mean_restricted_masks_per_point": branch_solves / point_count,
            "kkt_fallback_point_count": fallback,
            "kkt_fallback_fraction": fallback / point_count,
        }
    return result, masks, restricted


def local_targets(cells, axis, subdivisions):
    fractions = np.linspace(0.0, 1.0, subdivisions + 1, dtype=np.float64)
    red = axis[cells[:, 0], None] * (1.0 - fractions) + axis[
        cells[:, 0] + 1, None
    ] * fractions
    green = axis[cells[:, 1], None] * (1.0 - fractions) + axis[
        cells[:, 1] + 1, None
    ] * fractions
    blue = axis[cells[:, 2], None] * (1.0 - fractions) + axis[
        cells[:, 2] + 1, None
    ] * fractions
    rr, gg, bb = np.meshgrid(
        np.arange(subdivisions + 1),
        np.arange(subdivisions + 1),
        np.arange(subdivisions + 1),
        indexing="ij",
    )
    return np.stack(
        [red[:, rr], green[:, gg], blue[:, bb]], axis=-1
    ).reshape(-1, 3)


def sample_local(blocks, points, cells, inverse, axis, subdivisions):
    low = axis[cells]
    high = axis[cells + 1]
    scaled = np.clip(
        (points - low) / np.maximum(high - low, 1e-30) * subdivisions,
        0.0,
        subdivisions - 1e-8,
    )
    lower = np.floor(scaled).astype(np.int16)
    upper = lower + 1
    fraction = scaled - lower
    output = np.zeros_like(points, dtype=np.float64)
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                weight = (
                    (fraction[:, 0] if red else 1.0 - fraction[:, 0])
                    * (fraction[:, 1] if green else 1.0 - fraction[:, 1])
                    * (fraction[:, 2] if blue else 1.0 - fraction[:, 2])
                )
                output += blocks[
                    inverse,
                    lower[:, 0] + red,
                    lower[:, 1] + green,
                    lower[:, 2] + blue,
                ] * weight[:, None]
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("printer", type=Path)
    parser.add_argument("residual", type=Path)
    parser.add_argument("axis", type=Path)
    parser.add_argument("--subdivisions", type=int, default=4)
    parser.add_argument("--disagreement-threshold", type=float, default=0.00025)
    parser.add_argument("--iterations", type=int, default=24)
    parser.add_argument("--restricted-kkt", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    v72_profile.apply(e)
    printer = np.load(args.printer, mmap_mode="r")
    residual = np.load(args.residual, mmap_mode="r")
    axis = np.load(args.axis).astype(np.float64)
    combined, node_mask = combined_atlas(printer, residual)
    risk = risk_cells(node_mask)
    points = audit_points()
    cubic, lower = tricubic_axis(combined, points, axis)
    linear, _ = trilinear_axis(combined, points, axis)
    lower = np.minimum(lower, np.asarray(risk.shape) - 1)
    disagreement = np.max(np.abs(cubic - linear), axis=1)
    flagged = (
        risk[lower[:, 0], lower[:, 1], lower[:, 2]]
        | (disagreement >= args.disagreement_threshold)
    )
    unique_cells, inverse = np.unique(lower[flagged], axis=0, return_inverse=True)

    build_started = time.perf_counter()
    targets = local_targets(unique_cells, axis, args.subdivisions)
    corner_mask_sets = np.zeros((unique_cells.shape[0], 8), dtype=bool)
    for corner_red in (0, 1):
        for corner_green in (0, 1):
            for corner_blue in (0, 1):
                corner_masks = node_mask[
                    unique_cells[:, 0] + corner_red,
                    unique_cells[:, 1] + corner_green,
                    unique_cells[:, 2] + corner_blue,
                ]
                corner_mask_sets[np.arange(unique_cells.shape[0]), corner_masks] = True
    node_count = (args.subdivisions + 1) ** 3
    target_allowed_masks = (
        np.repeat(corner_mask_sets, node_count, axis=0)
        if args.restricted_kkt
        else None
    )
    refined_flat, refined_masks, restricted_audit = solve_printer_batched(
        targets,
        args.iterations,
        allowed_masks=target_allowed_masks,
    )
    masks_by_block = refined_masks.reshape(unique_cells.shape[0], -1)
    refined_mask_covered = corner_mask_sets[
        np.arange(unique_cells.shape[0])[:, None], masks_by_block
    ]
    expanded_mask_sets = corner_mask_sets.copy()
    for mask in range(8):
        if not np.any(corner_mask_sets[:, mask]):
            continue
        present = corner_mask_sets[:, mask]
        for bit in (1, 2, 4):
            expanded_mask_sets[present, mask ^ bit] = True
    refined_mask_expanded_covered = expanded_mask_sets[
        np.arange(unique_cells.shape[0])[:, None], masks_by_block
    ]
    side = args.subdivisions + 1
    blocks = refined_flat.reshape(unique_cells.shape[0], side, side, side, 3)
    refined = sample_local(
        blocks,
        points[flagged],
        lower[flagged],
        inverse,
        axis,
        args.subdivisions,
    )
    build_seconds = time.perf_counter() - build_started
    approximate = cubic.copy()
    approximate[flagged] = refined
    exact_cmy, exact_mask, _ = solve_nnls(e, points)
    exact = printer_density_from_cmy(e, exact_cmy)
    error = approximate - exact
    absolute = np.abs(error)
    worst = np.unravel_index(np.argmax(absolute), absolute.shape)
    report = {
        "policy": "129_power2_combined_cubic_plus_local_exact_subdivision",
        "point_count": int(points.shape[0]),
        "flagged_point_fraction": float(np.mean(flagged)),
        "unique_refined_parent_cells": int(unique_cells.shape[0]),
        "subdivisions_per_axis": args.subdivisions,
        "solver_iterations": args.iterations,
        "restricted_kkt_enabled": args.restricted_kkt,
        "restricted_kkt_audit": restricted_audit,
        "refined_node_count_with_duplicates": int(targets.shape[0]),
        "refined_node_active_mask_counts": {
            str(int(mask)): int(count)
            for mask, count in zip(
                *np.unique(refined_masks, return_counts=True), strict=True
            )
        },
        "refined_winner_covered_by_parent_corner_masks_fraction": float(
            np.mean(refined_mask_covered)
        ),
        "refined_winner_outside_parent_corner_masks_count": int(
            np.count_nonzero(~refined_mask_covered)
        ),
        "refined_winner_covered_by_corner_plus_hamming1_fraction": float(
            np.mean(refined_mask_expanded_covered)
        ),
        "refined_winner_outside_corner_plus_hamming1_count": int(
            np.count_nonzero(~refined_mask_expanded_covered)
        ),
        "refinement_build_seconds": build_seconds,
        "maximum_absolute_printer_density_error": float(absolute[worst]),
        "p99_absolute_printer_density_error": float(np.percentile(absolute, 99)),
        "rms_printer_density_error": float(np.sqrt(np.mean(np.square(error)))),
        "worst_status_m_net_density": points[worst[0]].tolist(),
        "worst_output_record": ("red", "green", "blue")[worst[1]],
        "worst_exact_mask": int(exact_mask[worst[0]]),
        "quality_gate": 0.001,
        "quality_gate_pass": bool(float(absolute[worst]) < 0.001),
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
