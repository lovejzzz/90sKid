#!/usr/bin/env python3
"""Multi-seed V34 CPU versus V35 Metal formed-negative validation."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
from pathlib import Path

import cv2
import numpy as np

from analyze_v35_density_equivalence import moment_summary, welch_radial_bands
from benchmark_v35_pipeline import decode_frame
import emulsion_experiment as e
import v27_accel
import v34_profile
import v35_accel


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate(items: list[dict]) -> dict:
    std = np.array([item["moments"]["std"] for item in items])
    skew = np.array([item["moments"]["skew"] for item in items])
    kurtosis = np.array([item["moments"]["excess_kurtosis"] for item in items])
    nps = np.array([item["nps"]["normalized_power"] for item in items])
    times = np.array([item["seconds"] for item in items])
    return {
        "seconds_mean": float(times.mean()),
        "seconds_median": float(np.median(times)),
        "std_mean": std.mean(axis=0).tolist(),
        "std_between_seed_range": np.ptp(std, axis=0).tolist(),
        "skew_mean": skew.mean(axis=0).tolist(),
        "kurtosis_mean": kurtosis.mean(axis=0).tolist(),
        "kurtosis_between_seed_range": np.ptp(kurtosis, axis=0).tolist(),
        "normalized_nps_mean": nps.mean(axis=0).tolist(),
        "normalized_nps_between_seed_range_max": float(np.ptp(nps, axis=0).max()),
    }


def run_seeds(records: np.ndarray, mean: np.ndarray, seeds: list[int]) -> list[dict]:
    items = []
    for frame_index in seeds:
        started = time.perf_counter()
        formed = e.form_5279_multilayer_record_density(
            records, frame_index, 1.0, 1, mean
        )
        seconds = time.perf_counter() - started
        residual = np.asarray(formed - mean, dtype=np.float32)
        items.append(
            {
                "frame_index": frame_index,
                "seconds": seconds,
                "moments": moment_summary(residual),
                "nps": welch_radial_bands(residual),
            }
        )
        del formed, residual
        gc.collect()
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=4)
    parser.add_argument("--opencv-threads", type=int, default=12)
    parser.add_argument("--array-workers", type=int, default=12)
    parser.add_argument(
        "--metal-mode", choices=("inverse", "bernoulli"), default="inverse"
    )
    args = parser.parse_args()
    v34_profile.apply(e)
    cv2.setNumThreads(args.opencv_threads)
    v27_accel.apply(
        e,
        numba_threads=min(args.array_workers, 12),
        array_workers=args.array_workers,
        exact_only=True,
    )
    v27_accel.warm(e)
    raw = decode_frame(args.source, args.decoder, 0, args.cache)
    film = e.scene_to_5279_film_rgb(raw, 0.45, v34_profile.PROFILE["raw_colour"], True, "photochemical")
    records = e.film_records_from_rgb(film)
    mean = e.develop_5279_record_density(records)
    del film, raw
    seeds = list(range(args.seeds))
    cpu = run_seeds(records, mean, seeds)
    v35_accel.apply_metal_binomial(e, mode=args.metal_mode)
    v35_accel.warm_metal_binomial(args.metal_mode)
    metal = run_seeds(records, mean, seeds)
    cpu_aggregate = aggregate(cpu)
    metal_aggregate = aggregate(metal)
    cpu_std = np.array(cpu_aggregate["std_mean"])
    metal_std = np.array(metal_aggregate["std_mean"])
    cpu_nps = np.array(cpu_aggregate["normalized_nps_mean"])
    metal_nps = np.array(metal_aggregate["normalized_nps_mean"])
    result = {
        "metal_mode": args.metal_mode,
        "provenance": {
            "source": str(args.source),
            "source_sha256": sha256(args.source),
            "algorithm_sha256": sha256(Path(e.__file__)),
            "v35_accel_sha256": sha256(Path(v35_accel.__file__)),
            "metal_bridge_source_sha256": sha256(
                Path(v35_accel.metal_binomial_bridge.SOURCE)
            ),
        },
        "seeds": seeds,
        "cpu": {"aggregate": cpu_aggregate, "per_seed": cpu},
        "metal": {"aggregate": metal_aggregate, "per_seed": metal},
        "comparison": {
            "speedup_formed_negative": (
                cpu_aggregate["seconds_median"] / metal_aggregate["seconds_median"]
            ),
            "std_ratio_metal_over_cpu": (metal_std / cpu_std).tolist(),
            "maximum_absolute_mean_normalized_nps_band_delta": float(
                np.max(np.abs(metal_nps - cpu_nps))
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, indent=2) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"cpu": cpu_aggregate, "metal": metal_aggregate, "comparison": result["comparison"]}, indent=2))


if __name__ == "__main__":
    main()
