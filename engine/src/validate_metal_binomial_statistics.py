#!/usr/bin/env python3
"""Distribution, spatial-independence and temporal-independence checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

import metal_binomial_bridge as metal


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    x = a.astype(np.float64).ravel()
    y = b.astype(np.float64).ravel()
    x -= x.mean()
    y -= y.mean()
    return float(np.dot(x, y) / math.sqrt(np.dot(x, x) * np.dot(y, y)))


def binomial_pmf(n: int, p: float) -> np.ndarray:
    return np.array(
        [math.comb(n, k) * p**k * (1.0 - p) ** (n - k) for k in range(n + 1)],
        dtype=np.float64,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mode", choices=("inverse", "bernoulli"), default="inverse")
    parser.add_argument("--trials", default="2,5,10,17,27")
    parser.add_argument(
        "--probabilities", default="0.001,0.02,0.1,0.5,0.9,0.98,0.999"
    )
    args = parser.parse_args()
    trial_values = [int(value) for value in args.trials.split(",")]
    probability_values = [
        float(value) for value in args.probabilities.split(",")
    ]
    cases = []
    for trials in trial_values:
        for probability_value in probability_values:
            probability = np.full(
                (args.size, args.size), probability_value, dtype=np.float32
            )
            seed = 35_000_000 + trials * 1000 + int(probability_value * 1000)
            first = metal.sample(probability, trials, seed, mode=args.mode)
            second = metal.sample(probability, trials, seed + 1, mode=args.mode)
            sample_mean = float(first.mean(dtype=np.float64))
            sample_variance = float(first.var(dtype=np.float64))
            expected_mean = trials * probability_value
            expected_variance = trials * probability_value * (1.0 - probability_value)
            count = first.size
            mean_z = (sample_mean - expected_mean) / math.sqrt(
                expected_variance / count
            )
            histogram = np.bincount(first.astype(np.int32).ravel(), minlength=trials + 1)
            expected_histogram = binomial_pmf(trials, probability_value) * count
            valid = expected_histogram >= 25.0
            histogram_z = (histogram[valid] - expected_histogram[valid]) / np.sqrt(
                expected_histogram[valid]
            )
            cases.append(
                {
                    "trials": trials,
                    "probability": probability_value,
                    "mean_z": float(mean_z),
                    "variance_ratio": sample_variance / expected_variance,
                    "maximum_histogram_z_expected_count_ge_25": float(
                        np.max(np.abs(histogram_z)) if histogram_z.size else 0.0
                    ),
                    "horizontal_lag1_correlation": correlation(first[:, :-1], first[:, 1:]),
                    "vertical_lag1_correlation": correlation(first[:-1], first[1:]),
                    "temporal_seed_correlation": correlation(first, second),
                }
            )
    maxima = {
        "absolute_mean_z": max(abs(case["mean_z"]) for case in cases),
        "absolute_variance_ratio_error": max(
            abs(case["variance_ratio"] - 1.0) for case in cases
        ),
        "absolute_histogram_z": max(
            case["maximum_histogram_z_expected_count_ge_25"] for case in cases
        ),
        "absolute_spatial_lag1_correlation": max(
            max(
                abs(case["horizontal_lag1_correlation"]),
                abs(case["vertical_lag1_correlation"]),
            )
            for case in cases
        ),
        "absolute_temporal_seed_correlation": max(
            abs(case["temporal_seed_correlation"]) for case in cases
        ),
    }
    result = {
        "mode": args.mode,
        "claim": (
            "Philox uint32 Bernoulli trials against a fixed-point float32 "
            "probability threshold"
            if args.mode == "bernoulli"
            else "24-bit-uniform inverse-CDF binomial"
        ),
        "sample_count_per_case": args.size**2,
        "trial_values": trial_values,
        "probability_values": probability_values,
        "provenance": {
            "bridge_python_sha256": sha256(Path(metal.__file__)),
            "bridge_source_sha256": sha256(Path(metal.SOURCE)),
        },
        "maxima": maxima,
        "cases": cases,
    }
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
