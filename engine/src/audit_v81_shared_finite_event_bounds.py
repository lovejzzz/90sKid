#!/usr/bin/env python3
"""Audit exact Bernoulli bounds for a shared finite-event grain prior.

V80 showed that post-formation covariance mixing violates finite density and
higher-order tails.  V81 asks what positive dependence is even mathematically
possible before density formation while preserving every fast/medium/slow
activation probability exactly.  It is an analytic uncertainty audit only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from emulsion5279 import legacy
import v72_profile


RECORD_NAMES = ("red", "green", "blue")
POPULATION_NAMES = ("fast", "medium", "slow")
RECORD_PAIRS = ((0, 1), (0, 2), (1, 2))
LOG_EXPOSURES = np.arange(-4.0, 0.751, 0.25, dtype=np.float64)
KEY_LOG_EXPOSURES = (-3.0, -2.0, -1.0, 0.0, 0.5)
TARGET_CORRELATIONS = (0.80, 0.90, 0.95, 0.99)
ALPHA_ENDPOINTS = (0.0, 0.25, 0.50, 0.75, 1.0)


def bernoulli_correlation_bounds(p: float, q: float) -> tuple[float, float]:
    denominator = np.sqrt(max(p * (1.0 - p) * q * (1.0 - q), 1e-30))
    minimum_joint = max(0.0, p + q - 1.0)
    maximum_joint = min(p, q)
    return (
        float((minimum_joint - p * q) / denominator),
        float((maximum_joint - p * q) / denominator),
    )


def shared_event_statistics(p: float, q: float, alpha: float) -> dict[str, float]:
    """Mixture of one common latent uniform and independent uniforms."""
    independent_joint = p * q
    common_joint = min(p, q)
    joint = alpha * common_joint + (1.0 - alpha) * independent_joint
    denominator = np.sqrt(max(p * (1.0 - p) * q * (1.0 - q), 1e-30))
    return {
        "joint_activation_probability": float(joint),
        "covariance": float(joint - independent_joint),
        "correlation": float((joint - independent_joint) / denominator),
    }


def row_for_log_exposure(log_exposure: float) -> dict[str, object]:
    e = legacy.model
    probabilities = e.subemulsion_activation_probabilities(
        np.full((3,), log_exposure, dtype=np.float32)
    ).astype(np.float64)
    pair_rows: list[dict[str, object]] = []
    for population, population_name in enumerate(POPULATION_NAMES):
        for left, right in RECORD_PAIRS:
            p = float(probabilities[left, population])
            q = float(probabilities[right, population])
            lower, upper = bernoulli_correlation_bounds(p, q)
            pair_rows.append(
                {
                    "population": population_name,
                    "record_pair": [RECORD_NAMES[left], RECORD_NAMES[right]],
                    "activation_probabilities": [p, q],
                    "minimum_correlation": lower,
                    "maximum_positive_correlation": upper,
                    "shared_event_alpha_endpoints": {
                        str(alpha): shared_event_statistics(p, q, alpha)
                        for alpha in ALPHA_ENDPOINTS
                    },
                    "target_feasibility": {
                        str(target): {
                            "feasible": bool(target <= upper + 1e-12),
                            "required_alpha_if_feasible": (
                                float(target / upper)
                                if target <= upper + 1e-12 and upper > 0.0
                                else None
                            ),
                        }
                        for target in TARGET_CORRELATIONS
                    },
                }
            )
    upper_values = np.asarray(
        [row["maximum_positive_correlation"] for row in pair_rows],
        dtype=np.float64,
    )
    return {
        "log_exposure": log_exposure,
        "activation_probability_by_record_population": {
            record: {
                population: float(probabilities[record_index, population_index])
                for population_index, population in enumerate(POPULATION_NAMES)
            }
            for record_index, record in enumerate(RECORD_NAMES)
        },
        "pair_bounds": pair_rows,
        "maximum_positive_correlation_range": [
            float(np.min(upper_values)),
            float(np.max(upper_values)),
        ],
    }


def measure() -> dict[str, object]:
    v72_profile.apply(legacy.model)
    rows = [row_for_log_exposure(float(value)) for value in LOG_EXPOSURES]
    all_pairs = [
        pair for row in rows for pair in row["pair_bounds"]
    ]
    key_rows = {
        str(value): next(
            row for row in rows if abs(row["log_exposure"] - value) < 1e-9
        )
        for value in KEY_LOG_EXPOSURES
    }
    feasibility: dict[str, object] = {}
    for target in TARGET_CORRELATIONS:
        feasible = [
            pair["maximum_positive_correlation"] >= target - 1e-12
            for pair in all_pairs
        ]
        feasibility[str(target)] = {
            "feasible_pair_exposure_count": int(np.sum(feasible)),
            "total_pair_exposure_count": len(feasible),
            "fraction": float(np.mean(feasible)),
        }

    return {
        "audit": "V81 exact shared finite-event Bernoulli bounds",
        "profile": "V72 activation probabilities",
        "image_change": "none; analytic uncertainty boundary only",
        "shared_event_family": {
            "construction": (
                "With probability alpha, all matched record populations test "
                "their own p against one common U(0,1); otherwise they use "
                "independent uniforms."
            ),
            "marginal_activation": "exact Bernoulli(p) for every record",
            "pair_covariance": "alpha * (min(p_i,p_j) - p_i*p_j)",
            "pair_correlation": "alpha * Frechet_positive_maximum",
            "finite_and_nonnegative": True,
        },
        "global_target_feasibility": feasibility,
        "key_exposure_rows": key_rows,
        "all_exposure_rows": rows,
        "evidence_boundary": (
            "The construction is a mathematically valid positive-dependence "
            "bound. Public 5279 data do not show that physical sites align "
            "across records, that dependence is symmetric, or that one alpha "
            "applies across speed population, spatial frequency and exposure."
        ),
        "decision": (
            "Use shared finite Bernoulli events, not completed-density mixing, "
            "as the architecture for any future covariance uncertainty test. "
            "Do not promote an alpha: even alpha=1 cannot reach an arbitrary "
            "common correlation when record activation probabilities differ, "
            "and real 5279 cross-population topology remains unmeasured."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = measure()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
