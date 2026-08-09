#!/usr/bin/env python3
"""Measure exact row-striped V27 pointwise kernels in a fresh process."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v27_accel
import v27_profile


def digest(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).view(np.uint8)).hexdigest()


def measure(function, source: np.ndarray, repeats: int) -> tuple[np.ndarray, list[float]]:
    times: list[float] = []
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = function(source)
        times.append(time.perf_counter() - started)
    assert result is not None
    return result, times


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()

    v27_profile.apply(e)
    v27_accel.apply(
        e,
        numba_threads=1,
        array_workers=args.workers,
        exact_only=True,
    )
    source = np.asarray(np.load(args.source, mmap_mode="r"), dtype=np.float32)
    density, density_seconds = measure(
        e.record_densities_from_log_exposure, source, args.repeats
    )
    activation, activation_seconds = measure(
        e.subemulsion_activation_probabilities, source, args.repeats
    )
    print(
        json.dumps(
            {
                "workers": args.workers,
                "density_seconds": density_seconds,
                "activation_seconds": activation_seconds,
                "density_sha256": digest(density),
                "activation_sha256": digest(activation),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
