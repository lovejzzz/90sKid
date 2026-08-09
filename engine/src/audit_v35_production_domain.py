#!/usr/bin/env python3
"""Record the actual V35 finite-site probability/trial/seed domain.

This is a provenance and validation input, not an image-model operation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import metal_binomial_bridge
import v35_accel
import v35_profile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decode_frame(source: Path, decoder: Path, frame: int) -> np.ndarray:
    width, height, _ = e.probe_video(source)
    process = subprocess.Popen(
        [str(decoder), str(source), str(frame), "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    payload = process.stdout.read(width * height * 3 * 4)
    stderr = process.stderr.read().decode("utf-8", errors="replace")
    if process.wait() != 0 or len(payload) != width * height * 3 * 4:
        raise RuntimeError(f"decode failed for {source}: {stderr}")
    return np.frombuffer(payload, dtype="<f4").reshape(height, width, 3).copy()


def class_counts() -> list[dict[str, object]]:
    rows = []
    for channel in range(3):
        for population in range(3):
            total = int(
                max(
                    1,
                    round(
                        float(
                            e.SUBEMULSION_SITE_COUNT_PX_5760_RGB[
                                channel, population
                            ]
                        )
                    ),
                )
            )
            fractions = (
                e.GRAIN_SIZE_CLASS_FRACTIONS
                if e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION is None
                else e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION[population]
            )
            raw = fractions * total
            counts = np.maximum(np.floor(raw).astype(np.int32), 1)
            while int(counts.sum()) < total:
                counts[int(np.argmax(raw - counts))] += 1
            while int(counts.sum()) > total:
                removable = np.where(counts > 1, counts, 0)
                counts[int(np.argmax(removable))] -= 1
            rows.append(
                {
                    "channel": channel,
                    "population": population,
                    "population_sites": total,
                    "class_trials": counts.tolist(),
                }
            )
    return rows


def probability_domain(raw: np.ndarray) -> list[dict[str, object]]:
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour=v35_profile.PROFILE["raw_colour"],
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    records = e.film_records_from_rgb(film)
    log_exposure = np.log10(np.maximum(records, 1e-8)) - 1.0
    activations = e.subemulsion_activation_probabilities(log_exposure)
    rows = []
    for channel in range(3):
        for population in range(3):
            plane = activations[..., channel, population]
            sample = plane[::8, ::8].astype(np.float64, copy=False)
            rows.append(
                {
                    "channel": channel,
                    "population": population,
                    "minimum": float(np.min(plane)),
                    "maximum": float(np.max(plane)),
                    "exact_zero_count": int(np.count_nonzero(plane == 0.0)),
                    "exact_one_count": int(np.count_nonzero(plane == 1.0)),
                    "sample_stride": 8,
                    "sample_percentiles": {
                        str(q): float(np.percentile(sample, q))
                        for q in (0.0001, 0.001, 0.01, 0.1, 1, 50, 99, 99.9, 99.99, 99.9999)
                    },
                }
            )
    return rows


def seed_audit(frame_count: int = 1000) -> dict[str, object]:
    seeds = []
    for frame in range(frame_count):
        for channel in range(3):
            for population in range(3):
                for size_class in range(5):
                    seeds.append(
                        30_000_000
                        + frame * 10_000
                        + channel * 1_000
                        + population * 100
                        + size_class
                    )
    unique = len(set(seeds))
    return {
        "formula": (
            "30000000 + frame*10000 + channel*1000 + "
            "population*100 + size_class"
        ),
        "frames_checked": frame_count,
        "seed_count": len(seeds),
        "unique_seed_count": unique,
        "collisions": len(seeds) - unique,
        "minimum": min(seeds),
        "maximum": max(seeds),
    }


def threshold_u32(probability: float) -> int:
    value = np.float32(probability)
    if value <= 0.0:
        return 0
    if value >= 1.0:
        return 2**32
    bits = int(value.view(np.uint32))
    exponent = ((bits >> 23) & 0xFF) - 127
    significand = (bits & 0x7FFFFF) | 0x800000
    shift = exponent + 9
    return significand << shift if shift >= 0 else significand >> (-shift)


def threshold_audit(source_results: list[dict[str, object]]) -> dict[str, object]:
    values = set()
    for source in source_results:
        for plane in source["probability_domain"]:
            values.add(float(plane["minimum"]))
            values.add(float(plane["maximum"]))
            values.update(float(value) for value in plane["sample_percentiles"].values())
    rows = []
    for value in sorted(values):
        threshold = threshold_u32(value)
        represented = threshold / 2**32
        rows.append(
            {
                "float32_probability": float(np.float32(value)),
                "u32_threshold": threshold,
                "represented_probability": represented,
                "absolute_error": abs(represented - float(np.float32(value))),
            }
        )
    return {
        "contract": (
            "success when Philox uint32 < floor(float32_probability * 2^32)"
        ),
        "maximum_absolute_probability_error": max(
            row["absolute_error"] for row in rows
        ),
        "theoretical_error_bound": 1.0 / 2**32,
        "tested_boundaries_and_percentiles": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--frame", type=int, default=0)
    args = parser.parse_args()

    v35_profile.apply(e)
    source_results = []
    for source in args.sources:
        raw = decode_frame(source, args.decoder, args.frame)
        source_results.append(
            {
                "path": str(source),
                "sha256": sha256(source),
                "frame": args.frame,
                "dimensions": [raw.shape[1], raw.shape[0]],
                "probability_domain": probability_domain(raw),
            }
        )
        del raw

    result = {
        "claim": (
            "Production-domain audit for the statistically validated 24-bit "
            "uniform inverse-CDF sampler; not an archive-exact claim"
        ),
        "provenance": {
            "algorithm_sha256": sha256(Path(e.__file__)),
            "profile_sha256": sha256(Path(v35_profile.__file__)),
            "v35_accel_sha256": sha256(Path(v35_accel.__file__)),
            "metal_bridge_python_sha256": sha256(
                Path(metal_binomial_bridge.__file__)
            ),
            "metal_bridge_source_sha256": sha256(
                Path(metal_binomial_bridge.SOURCE)
            ),
            "decoder_sha256": sha256(args.decoder),
        },
        "class_count_domain": class_counts(),
        "unique_class_trial_counts": sorted(
            {
                value
                for row in class_counts()
                for value in row["class_trials"]
            }
        ),
        "seed_audit": seed_audit(),
        "bernoulli_threshold_audit": threshold_audit(source_results),
        "sources": source_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
