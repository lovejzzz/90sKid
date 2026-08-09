#!/usr/bin/env python3
"""Benchmark safe per-flight Metal submission against serialized submission."""

from __future__ import annotations

import argparse
import json
import time

import numpy as np

import metal_gaussian_bridge as metal


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=5760)
    parser.add_argument("--height", type=int, default=4320)
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--sigma", type=float, default=18.0)
    args = parser.parse_args()
    if args.count < 1:
        raise ValueError("count must be positive")

    shape = (args.height, args.width)
    generator = np.random.default_rng(5279)
    sources: list[np.ndarray] = []
    for _ in range(args.count):
        source = metal.aligned_empty(shape)
        source[:] = generator.random(shape, dtype=np.float32)
        sources.append(source)

    warm = metal.submit_gaussian_async(sources[0], args.sigma)
    warm.wait()

    started = time.perf_counter()
    serialized: list[np.ndarray] = []
    for source in sources:
        flight = metal.submit_gaussian_async(source, args.sigma)
        serialized.append(flight.wait().copy())
    serialized_seconds = time.perf_counter() - started

    started = time.perf_counter()
    flights = [
        metal.submit_gaussian_async(source, args.sigma) for source in sources
    ]
    submit_seconds = time.perf_counter() - started
    batched = [flight.wait() for flight in flights]
    batched_seconds = time.perf_counter() - started
    maximum_differences = [
        float(np.max(np.abs(reference - candidate)))
        for reference, candidate in zip(serialized, batched, strict=True)
    ]
    result = {
        "shape": list(shape),
        "count": args.count,
        "sigma": args.sigma,
        "serialized_seconds": serialized_seconds,
        "batched_submit_seconds": submit_seconds,
        "batched_seconds": batched_seconds,
        "speedup": serialized_seconds / batched_seconds,
        "flight_seconds": [flight.bridge_seconds for flight in flights],
        "max_abs_batched_vs_serialized": maximum_differences,
        "bit_identical": all(value == 0.0 for value in maximum_differences),
        "lifetime_contract": (
            "each Python flight owns input/output/weights until wait completes"
        ),
    }
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
