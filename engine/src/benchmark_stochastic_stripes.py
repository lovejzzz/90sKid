#!/usr/bin/env python3
"""Benchmark deterministic binomial stripe layouts on a cached V27 frame."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v27_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--mean-density", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stripes", type=int, required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--opencv-threads", type=int, default=16)
    parser.add_argument("--frame-index", type=int, default=0)
    args = parser.parse_args()

    v27_profile.apply(e)
    cv2.setNumThreads(args.opencv_threads)
    e.BINOMIAL_RANDOM_STRIPES = args.stripes
    e.BINOMIAL_PARALLEL_WORKERS = args.workers
    records = np.load(args.records, mmap_mode="r")
    mean_density = np.load(args.mean_density, mmap_mode="r")
    started = time.perf_counter()
    formed = e.form_5279_multilayer_record_density(
        records,
        args.frame_index,
        1.0,
        1,
        precomputed_mean_density=mean_density,
    )
    seconds = time.perf_counter() - started
    delta = formed - mean_density
    # Include seam-adjacent statistics to expose any stripe-boundary pathology.
    bounds = np.linspace(0, formed.shape[0], args.stripes + 1, dtype=np.int32)[1:-1]
    seam_rows = np.unique(
        np.clip(np.concatenate([bounds - 1, bounds, bounds + 1]), 0, formed.shape[0] - 1)
    )
    result = {
        "stripes": args.stripes,
        "workers": args.workers,
        "opencv_threads": args.opencv_threads,
        "seconds": seconds,
        "sha256_float32": hashlib.sha256(formed.tobytes()).hexdigest(),
        "delta_mean_rgb": [float(value) for value in delta.mean(axis=(0, 1))],
        "delta_std_rgb": [float(value) for value in delta.std(axis=(0, 1))],
        "delta_p01_rgb": [
            float(np.percentile(delta[..., channel], 1.0)) for channel in range(3)
        ],
        "delta_p99_rgb": [
            float(np.percentile(delta[..., channel], 99.0)) for channel in range(3)
        ],
        "seam_delta_mean_rgb": [
            float(value) for value in delta[seam_rows].mean(axis=(0, 1))
        ],
        "seam_delta_std_rgb": [
            float(value) for value in delta[seam_rows].std(axis=(0, 1))
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
