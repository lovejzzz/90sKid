#!/usr/bin/env python3
"""Audit three-record compatibility of finite Bernoulli activation priors.

V81 derived exact pairwise Frechet bounds and one valid all-record common-U
family.  V82 checks the missing condition: three pairwise-valid targets do not
necessarily define one nonnegative eight-cell RGB joint distribution.  This is
an analytic uncertainty audit only; it does not render or promote a sampler.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from emulsion5279 import legacy
import v72_profile


RECORD_NAMES = ("red", "green", "blue")
POPULATION_NAMES = ("fast", "medium", "slow")
LOG_EXPOSURES = np.arange(-4.0, 0.751, 0.25, dtype=np.float64)
KEY_LOG_EXPOSURES = (-3.0, -2.0, -1.0, 0.0, 0.5)
TARGET_EQUAL_CORRELATIONS = (0.80, 0.90, 0.95, 0.99)
PAIR_ALPHA_ENDPOINTS = (0.0, 0.25, 0.50, 0.75, 1.0)


def pair_joint_from_correlation(p: float, q: float, rho: float) -> float:
    return float(p * q + rho * np.sqrt(p * (1.0 - p) * q * (1.0 - q)))


def pair_joint_from_alpha(p: float, q: float, alpha: float) -> float:
    return float(p * q + alpha * (min(p, q) - p * q))


def pair_is_valid(p: float, q: float, joint: float, tol: float = 1e-12) -> bool:
    return max(0.0, p + q - 1.0) - tol <= joint <= min(p, q) + tol


def triple_interval(
    p: np.ndarray,
    pair_joints: tuple[float, float, float],
) -> tuple[float, float]:
    """Return the exact feasible interval for P(R=G=B=1)."""
    q_rg, q_rb, q_gb = pair_joints
    lower = max(
        0.0,
        q_rg + q_rb - float(p[0]),
        q_rg + q_gb - float(p[1]),
        q_rb + q_gb - float(p[2]),
    )
    upper = min(
        q_rg,
        q_rb,
        q_gb,
        1.0 - float(np.sum(p)) + q_rg + q_rb + q_gb,
    )
    return float(lower), float(upper)


def eight_cells(
    p: np.ndarray,
    pair_joints: tuple[float, float, float],
    triple: float,
) -> dict[str, float]:
    q_rg, q_rb, q_gb = pair_joints
    return {
        "111": triple,
        "110": q_rg - triple,
        "101": q_rb - triple,
        "011": q_gb - triple,
        "100": float(p[0]) - q_rg - q_rb + triple,
        "010": float(p[1]) - q_rg - q_gb + triple,
        "001": float(p[2]) - q_rb - q_gb + triple,
        "000": 1.0 - float(np.sum(p)) + q_rg + q_rb + q_gb - triple,
    }


def correlation_matrix(p: np.ndarray, pair_joints: tuple[float, float, float]) -> np.ndarray:
    matrix = np.eye(3, dtype=np.float64)
    for joint, (left, right) in zip(pair_joints, ((0, 1), (0, 2), (1, 2))):
        denominator = np.sqrt(
            max(
                float(p[left] * (1.0 - p[left]) * p[right] * (1.0 - p[right])),
                1e-30,
            )
        )
        matrix[left, right] = matrix[right, left] = (
            joint - float(p[left] * p[right])
        ) / denominator
    return matrix


def analyze_triplet(p: np.ndarray) -> dict[str, object]:
    equal_target: dict[str, object] = {}
    for rho in TARGET_EQUAL_CORRELATIONS:
        joints = tuple(
            pair_joint_from_correlation(float(p[left]), float(p[right]), rho)
            for left, right in ((0, 1), (0, 2), (1, 2))
        )
        pair_valid = all(
            pair_is_valid(float(p[left]), float(p[right]), joint)
            for joint, (left, right) in zip(joints, ((0, 1), (0, 2), (1, 2)))
        )
        lower, upper = triple_interval(p, joints)
        matrix = correlation_matrix(p, joints)
        equal_target[str(rho)] = {
            "all_three_pairs_frechet_valid": pair_valid,
            "joint_three_record_feasible": bool(pair_valid and lower <= upper + 1e-12),
            "triple_activation_interval": [lower, upper],
            "minimum_correlation_eigenvalue": float(np.min(np.linalg.eigvalsh(matrix))),
        }

    alpha_rows: list[dict[str, object]] = []
    for alpha_rg, alpha_rb, alpha_gb in itertools.product(PAIR_ALPHA_ENDPOINTS, repeat=3):
        alphas = (alpha_rg, alpha_rb, alpha_gb)
        joints = tuple(
            pair_joint_from_alpha(float(p[left]), float(p[right]), alpha)
            for alpha, (left, right) in zip(alphas, ((0, 1), (0, 2), (1, 2)))
        )
        lower, upper = triple_interval(p, joints)
        matrix = correlation_matrix(p, joints)
        feasible = lower <= upper + 1e-12
        alpha_rows.append(
            {
                "pair_alphas_rg_rb_gb": list(alphas),
                "joint_three_record_feasible": bool(feasible),
                "triple_interval_width": float(upper - lower),
                "minimum_correlation_eigenvalue": float(np.min(np.linalg.eigvalsh(matrix))),
                "psd_but_not_jointly_bernoulli": bool(
                    np.min(np.linalg.eigvalsh(matrix)) >= -1e-12 and not feasible
                ),
            }
        )

    common_alpha: dict[str, object] = {}
    for alpha in PAIR_ALPHA_ENDPOINTS:
        joints = tuple(
            pair_joint_from_alpha(float(p[left]), float(p[right]), alpha)
            for left, right in ((0, 1), (0, 2), (1, 2))
        )
        lower, upper = triple_interval(p, joints)
        # The V81 common-U/independent mixture has an explicit triple joint.
        triple = alpha * float(np.min(p)) + (1.0 - alpha) * float(np.prod(p))
        cells = eight_cells(p, joints, triple)
        common_alpha[str(alpha)] = {
            "triple_activation_probability": triple,
            "allowed_triple_interval": [lower, upper],
            "minimum_eight_cell_probability": float(min(cells.values())),
            "marginal_and_joint_valid": bool(
                lower - 1e-12 <= triple <= upper + 1e-12
                and min(cells.values()) >= -1e-12
                and abs(sum(cells.values()) - 1.0) <= 1e-12
            ),
        }

    return {
        "activation_probabilities_rgb": [float(value) for value in p],
        "equal_pair_correlation_targets": equal_target,
        "independent_pair_alpha_grid": {
            "tested_count": len(alpha_rows),
            "jointly_feasible_count": int(
                sum(row["joint_three_record_feasible"] for row in alpha_rows)
            ),
            "psd_but_not_jointly_bernoulli_count": int(
                sum(row["psd_but_not_jointly_bernoulli"] for row in alpha_rows)
            ),
            "rows": alpha_rows,
        },
        "single_common_alpha_family": common_alpha,
    }


def measure() -> dict[str, object]:
    v72_profile.apply(legacy.model)
    rows: list[dict[str, object]] = []
    for log_exposure in LOG_EXPOSURES:
        probabilities = legacy.model.subemulsion_activation_probabilities(
            np.full((3,), log_exposure, dtype=np.float32)
        ).astype(np.float64)
        rows.append(
            {
                "log_exposure": float(log_exposure),
                "populations": {
                    name: analyze_triplet(probabilities[:, index])
                    for index, name in enumerate(POPULATION_NAMES)
                },
            }
        )

    triplets = [
        population
        for row in rows
        for population in row["populations"].values()
    ]
    equal_summary: dict[str, object] = {}
    for rho in TARGET_EQUAL_CORRELATIONS:
        pair_valid = [
            triplet["equal_pair_correlation_targets"][str(rho)][
                "all_three_pairs_frechet_valid"
            ]
            for triplet in triplets
        ]
        jointly_valid = [
            triplet["equal_pair_correlation_targets"][str(rho)][
                "joint_three_record_feasible"
            ]
            for triplet in triplets
        ]
        equal_summary[str(rho)] = {
            "all_three_pairs_valid_triplets": int(sum(pair_valid)),
            "jointly_valid_triplets": int(sum(jointly_valid)),
            "total_triplets": len(triplets),
        }

    alpha_total = sum(
        triplet["independent_pair_alpha_grid"]["tested_count"]
        for triplet in triplets
    )
    alpha_feasible = sum(
        triplet["independent_pair_alpha_grid"]["jointly_feasible_count"]
        for triplet in triplets
    )
    psd_false_positive = sum(
        triplet["independent_pair_alpha_grid"]["psd_but_not_jointly_bernoulli_count"]
        for triplet in triplets
    )
    common_valid = all(
        endpoint["marginal_and_joint_valid"]
        for triplet in triplets
        for endpoint in triplet["single_common_alpha_family"].values()
    )

    return {
        "audit": "V82 three-record Bernoulli compatibility polytope",
        "profile": "V72 activation probabilities",
        "image_change": "none; analytic uncertainty boundary only",
        "triplet_count": len(triplets),
        "equal_pair_correlation_summary": equal_summary,
        "independent_pair_alpha_grid_summary": {
            "tested_triplet_parameter_sets": alpha_total,
            "jointly_feasible": alpha_feasible,
            "jointly_infeasible": alpha_total - alpha_feasible,
            "psd_but_not_jointly_bernoulli": psd_false_positive,
        },
        "single_common_alpha_family_valid_everywhere": common_valid,
        "key_exposure_rows": {
            str(value): next(
                row for row in rows if abs(row["log_exposure"] - value) < 1e-9
            )
            for value in KEY_LOG_EXPOSURES
        },
        "all_exposure_rows": rows,
        "decision": (
            "Do not expose three independent pair-correlation controls. Pairwise "
            "Frechet bounds and a positive-semidefinite correlation matrix are "
            "not sufficient for one nonnegative RGB Bernoulli distribution. The "
            "single common-alpha V81 family is jointly valid, but remains an "
            "unmeasured uncertainty coordinate and is not promoted to V72 pixels."
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
