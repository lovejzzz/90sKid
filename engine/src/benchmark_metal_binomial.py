#!/usr/bin/env python3
"""Time and statistically validate the research Metal binomial sampler."""

from __future__ import annotations

import argparse
import json
import time

import numpy as np

import metal_binomial_bridge as metal


def summarize(values: np.ndarray, probability: np.ndarray, trials: int) -> dict:
    expected_mean = trials * probability
    expected_variance = trials * probability * (1.0 - probability)
    residual = values - expected_mean
    return {
        "mean_residual": float(residual.mean()),
        "residual_variance": float(residual.var()),
        "expected_mean_variance": float(expected_variance.mean()),
        "variance_ratio": float(residual.var() / expected_variance.mean()),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=5760)
    parser.add_argument("--height", type=int, default=4320)
    parser.add_argument("--trials", type=int, default=17)
    parser.add_argument("--seed", type=int, default=30_000_000)
    parser.add_argument("--mode", choices=("inverse", "bernoulli"), default="bernoulli")
    args = parser.parse_args()
    y, x = np.mgrid[: args.height, : args.width]
    probability = (0.001 + 0.998 * x / max(args.width - 1, 1)).astype(np.float32)
    probability = np.ascontiguousarray(np.broadcast_to(probability, (args.height, args.width)))
    started = time.perf_counter()
    gpu = metal.sample(probability, args.trials, args.seed, args.mode)
    gpu_seconds = time.perf_counter() - started
    rng = np.random.default_rng(args.seed)
    started = time.perf_counter()
    cpu = rng.binomial(args.trials, probability).astype(np.float32)
    cpu_seconds = time.perf_counter() - started
    print(
        json.dumps(
            {
                "shape": list(probability.shape),
                "trials": args.trials,
                "mode": args.mode,
                "metal_seconds": gpu_seconds,
                "numpy_seconds": cpu_seconds,
                "speedup": cpu_seconds / gpu_seconds,
                "metal": summarize(gpu, probability, args.trials),
                "numpy": summarize(cpu, probability, args.trials),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
