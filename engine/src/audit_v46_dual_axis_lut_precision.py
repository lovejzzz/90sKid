#!/usr/bin/env python3
"""Test complementary uniform and toe-dense V46 active-set atlases."""

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
from v46_status_m_active_set import printer_density_from_cmy, solve_nnls


def atlas(printer, residual, axis, points):
    outputs = {}
    for name, sampler in (("linear", trilinear_axis), ("cubic", tricubic_axis)):
        best_residual = np.full(points.shape[0], np.inf, dtype=np.float64)
        best_printer = np.empty_like(points, dtype=np.float64)
        mask = np.zeros(points.shape[0], dtype=np.uint8)
        for branch in range(8):
            branch_residual, _ = sampler(
                residual[branch][..., None], points, axis
            )
            branch_printer, _ = sampler(printer[branch], points, axis)
            improved = branch_residual[:, 0] < best_residual
            best_residual[improved] = branch_residual[improved, 0]
            best_printer[improved] = branch_printer[improved]
            mask[improved] = branch
        outputs[name] = {
            "residual": best_residual,
            "printer": best_printer,
            "mask": mask,
        }
    outputs["disagreement"] = np.max(
        np.abs(outputs["cubic"]["printer"] - outputs["linear"]["printer"]),
        axis=1,
    )
    return outputs


def metrics(output, exact):
    error = np.asarray(output) - np.asarray(exact)
    absolute = np.abs(error)
    worst = np.unravel_index(np.argmax(absolute), absolute.shape)
    return {
        "maximum_absolute": float(absolute[worst]),
        "p99_absolute": float(np.percentile(absolute, 99)),
        "rms": float(np.sqrt(np.mean(np.square(error)))),
        "worst_point": int(worst[0]),
        "worst_output_record": ("red", "green", "blue")[worst[1]],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uniform-printer", type=Path, required=True)
    parser.add_argument("--uniform-residual", type=Path, required=True)
    parser.add_argument("--toe-printer", type=Path, required=True)
    parser.add_argument("--toe-residual", type=Path, required=True)
    parser.add_argument("--toe-axis", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    v72_profile.apply(e)
    uniform_printer = np.load(args.uniform_printer, mmap_mode="r")
    uniform_residual = np.load(args.uniform_residual, mmap_mode="r")
    toe_printer = np.load(args.toe_printer, mmap_mode="r")
    toe_residual = np.load(args.toe_residual, mmap_mode="r")
    uniform_axis = np.linspace(
        0.0, e.NEGATIVE_5279_MAX_RECORD_DENSITY,
        uniform_printer.shape[1], dtype=np.float64,
    )
    toe_axis = np.load(args.toe_axis).astype(np.float64)
    points = audit_points()
    started = time.perf_counter()
    uniform = atlas(uniform_printer, uniform_residual, uniform_axis, points)
    toe = atlas(toe_printer, toe_residual, toe_axis, points)
    atlas_seconds = time.perf_counter() - started
    exact_cmy, exact_mask, _ = solve_nnls(e, points)
    exact = printer_density_from_cmy(e, exact_cmy).astype(np.float64)

    rows = []
    minimum = np.min(points, axis=1)
    for threshold in (0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5):
        use_toe = minimum < threshold
        output = np.where(
            use_toe[:, None],
            toe["cubic"]["printer"],
            uniform["cubic"]["printer"],
        )
        row = {
            "policy": "toe_atlas_if_minimum_record_below_threshold",
            "threshold": threshold,
            "toe_fraction": float(np.mean(use_toe)),
            **metrics(output, exact),
        }
        row["worst_status_m_net_density"] = points[row["worst_point"]].tolist()
        row["worst_exact_mask"] = int(exact_mask[row["worst_point"]])
        rows.append(row)

    choose_disagreement = toe["disagreement"] < uniform["disagreement"]
    disagreement_output = np.where(
        choose_disagreement[:, None],
        toe["cubic"]["printer"],
        uniform["cubic"]["printer"],
    )
    disagreement_metrics = metrics(disagreement_output, exact)
    disagreement_metrics.update(
        {
            "toe_fraction": float(np.mean(choose_disagreement)),
            "worst_status_m_net_density": points[
                disagreement_metrics["worst_point"]
            ].tolist(),
        }
    )
    report = {
        "policy": "complementary_uniform_and_toe_dense_active_set_atlases",
        "point_count": int(points.shape[0]),
        "atlas_seconds": atlas_seconds,
        "uniform_cubic": metrics(uniform["cubic"]["printer"], exact),
        "toe_cubic": metrics(toe["cubic"]["printer"], exact),
        "minimum_record_threshold_sweep": rows,
        "minimum_linear_cubic_disagreement_selection": disagreement_metrics,
        "quality_gate": 0.001,
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
