#!/usr/bin/env python3
"""Audit V41's chart-bounded colour transport on calibration and holdout clips."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v40_profile
import v41_profile
from audit_t003_colorchecker import colour_residual_diagnostic


def transform_diagnostic(report: dict[str, object]) -> dict[str, object]:
    records = copy.deepcopy(report["patches"])
    source = np.asarray(
        [record["decoded_linear_bt2020_median"] for record in records],
        dtype=np.float32,
    )
    corrected = e.apply_input_chroma_residual(source)
    for record, value in zip(records, corrected):
        record["decoded_linear_bt2020_median"] = value.tolist()
    before_y = source @ e.BT2020_TO_XYZ_D65[1]
    after_y = corrected @ e.BT2020_TO_XYZ_D65[1]
    return {
        "before": report["colour_residual_diagnostic"],
        "after": colour_residual_diagnostic(records),
        "maximum_relative_scene_luminance_change": float(
            np.max(np.abs(after_y / np.maximum(before_y, 1e-8) - 1.0))
        ),
    }


def group_improvement(record: dict[str, object], group: str) -> dict[str, float]:
    before = record["before"][group]
    after = record["after"][group]
    return {
        "median_hue_error_reduction_degrees": float(
            before["median_absolute_hue_error_degrees"]
            - after["median_absolute_hue_error_degrees"]
        ),
        "maximum_hue_error_reduction_degrees": float(
            before["maximum_absolute_hue_error_degrees"]
            - after["maximum_absolute_hue_error_degrees"]
        ),
        "median_chroma_ratio_before": float(before["median_chroma_ratio"]),
        "median_chroma_ratio_after": float(after["median_chroma_ratio"]),
    }


def boundary_probe(report: dict[str, object]) -> dict[str, object]:
    source = np.asarray(
        [record["decoded_linear_bt2020_median"] for record in report["patches"]],
        dtype=np.float32,
    )
    corrected = e.apply_input_chroma_residual(source) * (2.0**0.45)
    film = e.bt2020_to_balanced_film_rgb(corrected)
    signed = film @ e.FILM_RECORD_SENSITIVITY_RGB.T
    clipped = np.maximum(film, 0.0) @ e.FILM_RECORD_SENSITIVITY_RGB.T
    v41 = e.film_records_from_rgb(film)
    valid = np.all(signed >= 0.0, axis=1)
    negative_basis = np.any(film < 0.0, axis=1)
    return {
        "negative_basis_patches": [
            int(index + 1) for index in np.flatnonzero(negative_basis)
        ],
        "record_positive_signed_patches": [
            int(index + 1) for index in np.flatnonzero(negative_basis & valid)
        ],
        "fallback_to_clipped_basis_patches": [
            int(index + 1) for index in np.flatnonzero(negative_basis & ~valid)
        ],
        "maximum_record_difference_vs_signed_on_valid_patches": float(
            np.max(np.abs(v41[valid] - signed[valid])) if np.any(valid) else 0.0
        ),
        "maximum_record_difference_vs_clipped_on_fallback_patches": float(
            np.max(np.abs(v41[~valid] - clipped[~valid])) if np.any(~valid) else 0.0
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("t003", type=Path)
    parser.add_argument("t005", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    reports = {
        "T003_calibration": json.loads(args.t003.read_text(encoding="utf-8")),
        "T005_holdout": json.loads(args.t005.read_text(encoding="utf-8")),
    }
    v41_profile.apply(e)
    transformed = {name: transform_diagnostic(report) for name, report in reports.items()}
    groups = {
        "synthetic": "synthetic_primary_patches_7_to_12",
        "natural": "natural_colour_patches_13_to_18",
    }
    improvements = {
        name: {
            label: group_improvement(record, key)
            for label, key in groups.items()
        }
        for name, record in transformed.items()
    }
    gates = {
        "T003_synthetic_median_hue_improves": improvements["T003_calibration"]["synthetic"]["median_hue_error_reduction_degrees"] > 0.0,
        "T003_natural_median_hue_improves": improvements["T003_calibration"]["natural"]["median_hue_error_reduction_degrees"] > 0.0,
        "T005_holdout_synthetic_median_hue_improves": improvements["T005_holdout"]["synthetic"]["median_hue_error_reduction_degrees"] > 0.0,
        "T005_holdout_natural_median_hue_improves": improvements["T005_holdout"]["natural"]["median_hue_error_reduction_degrees"] > 0.0,
        "both_clips_natural_median_chroma_error_improves": all(
            abs(improvements[name]["natural"]["median_chroma_ratio_after"] - 1.0)
            < abs(improvements[name]["natural"]["median_chroma_ratio_before"] - 1.0)
            for name in improvements
        ),
        "scene_luminance_relative_change_below_1e_5": all(
            record["maximum_relative_scene_luminance_change"] < 1e-5
            for record in transformed.values()
        ),
    }
    report = {
        "audit": "V41 chart-bounded colour transport",
        "authority": (
            "T003 fit plus T005 independent holdout; both are 5500 K, ISO 500 "
            "outdoor captures. The residual remains provisional until measured "
            "uniform D65/tungsten controls."
        ),
        "matrix_D50_chroma_only": v41_profile.INPUT_CHROMA_RESIDUAL_D50.tolist(),
        "ridge_lambda": 0.003,
        "strength": v41_profile.INPUT_CHROMA_RESIDUAL_STRENGTH,
        "clips": transformed,
        "improvements": improvements,
        "record_boundary": {
            name: boundary_probe(source) for name, source in reports.items()
        },
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"improvements": improvements, "gates": gates}, indent=2))
    if not report["all_gates_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
