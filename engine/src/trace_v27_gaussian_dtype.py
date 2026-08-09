#!/usr/bin/env python3
"""Trace Gaussian input dtype by V27 stage without changing output."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

import benchmark_v27_pipeline as benchmark
import emulsion_experiment as e
import v27_accel
import v27_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("frame", type=Path)
    args = parser.parse_args()
    v27_profile.apply(e)
    cv2.setNumThreads(16)
    e.BINOMIAL_PARALLEL_WORKERS = 12
    v27_accel.apply(e, numba_threads=12, array_workers=12, exact_only=True)
    source = np.asarray(np.load(args.frame, mmap_mode="r"), dtype=np.float32)
    reference = cv2.GaussianBlur
    stage = "unknown"
    rows: list[dict[str, object]] = []

    def traced(array, ksize, sigma_x, *positional, **keywords):
        started = time.perf_counter()
        result = reference(array, ksize, sigma_x, *positional, **keywords)
        rows.append(
            {
                "stage": stage,
                "shape": list(np.asarray(array).shape),
                "dtype": str(np.asarray(array).dtype),
                "sigma": float(sigma_x),
                "seconds": time.perf_counter() - started,
            }
        )
        return result

    cv2.GaussianBlur = traced
    stages: dict[str, float] = {}

    def run(name, function, *values):
        nonlocal stage
        stage = name
        started = time.perf_counter()
        result = function(*values)
        stages[name] = time.perf_counter() - started
        return result

    film = run(
        "scene_to_film",
        e.scene_to_5279_film_rgb,
        source,
        0.45,
        "panasonic_official",
        True,
        "photochemical",
    )
    records = run("film_records", e.film_records_from_rgb, film)
    mean = run("mean_negative", e.develop_5279_record_density, records)
    formed = run(
        "stochastic_emulsion",
        e.form_5279_multilayer_record_density,
        records,
        0,
        1.0,
        1,
        mean,
    )
    run(
        "scan_render",
        e.reconstruct_density_pair_to_display,
        mean,
        formed,
        0,
        1.0,
        "cineon_bluray",
        "legacy_bt709_oetf",
    )
    summary: dict[str, dict[str, dict[str, float | int]]] = {}
    for row in rows:
        stage_entry = summary.setdefault(str(row["stage"]), {})
        dtype_entry = stage_entry.setdefault(
            str(row["dtype"]), {"calls": 0, "seconds": 0.0}
        )
        dtype_entry["calls"] = int(dtype_entry["calls"]) + 1
        dtype_entry["seconds"] = float(dtype_entry["seconds"]) + float(
            row["seconds"]
        )
    print(json.dumps({"stage_seconds": stages, "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
