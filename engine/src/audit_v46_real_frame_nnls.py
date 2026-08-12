#!/usr/bin/env python3
"""Measure the V46 active-set inverse on sampled real formed negatives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from engine.emulsion5279 import legacy
from engine.emulsion5279.contracts import EngineConfig, EngineMode
from engine.emulsion5279.io import ProResRawDecoder
from engine.emulsion5279.pipeline import Emulsion5279Engine
from v46_status_m_active_set import printer_density_from_cmy, solve_nnls


DEFAULT_FRAMES = {"T020": 0, "T032": 0, "T007": 276}


def sample_indices(density: np.ndarray, count: int, seed: int) -> np.ndarray:
    flat = np.asarray(density, dtype=np.float32).reshape(-1, 3)
    rng = np.random.default_rng(seed)
    random_count = max(count - 3_000, 1)
    chosen = [rng.integers(0, flat.shape[0], size=random_count)]
    with np.errstate(all="ignore"):
        luma = flat @ np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    for values in (luma, flat[:, 0], flat[:, 1], flat[:, 2]):
        order = np.argpartition(values, (499, values.size - 500))
        chosen.append(order[:500])
        chosen.append(order[-500:])
    indices = np.unique(np.concatenate(chosen))
    if indices.size > count:
        indices = rng.choice(indices, size=count, replace=False)
    return np.sort(indices)


def summarize_array(values: np.ndarray) -> dict[str, float]:
    source = np.asarray(values, dtype=np.float64)
    return {
        "maximum": float(np.max(source)),
        "p99": float(np.percentile(source, 99)),
        "median": float(np.median(source)),
        "mean": float(np.mean(source)),
    }


def audit_density(model, density: np.ndarray, count: int, seed: int) -> dict[str, object]:
    flat = np.asarray(density, dtype=np.float32).reshape(-1, 3)
    indices = sample_indices(density, count, seed)
    target = np.maximum(flat[indices] - model.SENSITO_DMIN_RGB, 0.0).astype(
        np.float64
    )
    old_started = time.perf_counter()
    old_cmy = model.solve_5279_analytical_cmy_from_status_m_net_density(target)
    old_seconds = time.perf_counter() - old_started
    old_forward = model.negative_5279_status_m_net_density_from_analytical_cmy(
        old_cmy
    ).astype(np.float64)
    old_sse = np.sum(np.square(old_forward - target), axis=1)
    old_printer = printer_density_from_cmy(model, old_cmy).astype(np.float64)

    new_started = time.perf_counter()
    new_cmy, masks, new_sse = solve_nnls(model, target)
    new_seconds = time.perf_counter() - new_started
    new_printer = printer_density_from_cmy(model, new_cmy).astype(np.float64)
    delta = new_printer - old_printer
    absolute_delta = np.abs(delta)
    worst = np.unravel_index(np.argmax(absolute_delta), absolute_delta.shape)
    return {
        "sample_count": int(target.shape[0]),
        "old_seconds": old_seconds,
        "v46_exact_seconds": new_seconds,
        "old_status_m_squared_residual": summarize_array(old_sse),
        "v46_status_m_squared_residual": summarize_array(new_sse),
        "strictly_improves_fraction": float(np.mean(new_sse < old_sse - 1e-12)),
        "worsens_count": int(np.count_nonzero(new_sse > old_sse + 1e-12)),
        "active_mask_counts": {
            str(int(mask)): int(number)
            for mask, number in zip(*np.unique(masks, return_counts=True), strict=True)
        },
        "printer_density_delta": {
            "maximum_absolute": float(absolute_delta[worst]),
            "p99_absolute": float(np.percentile(absolute_delta, 99)),
            "median_absolute": float(np.median(absolute_delta)),
            "rms": float(np.sqrt(np.mean(np.square(delta)))),
            "worst_status_m_net_density": target[worst[0]].tolist(),
            "worst_output_record": ("red", "green", "blue")[worst[1]],
            "worst_signed": float(delta[worst]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--source", action="append", type=Path, required=True)
    parser.add_argument("--sample-count", type=int, default=20_000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = EngineConfig(
        profile="v72",
        mode=EngineMode.PRODUCTION_METAL,
        observer_branch_workers=1,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    model = legacy.model
    report: dict[str, object] = {
        "audit": "V46 real-frame Status-M active-set impact",
        "profile": "v72 evidence-minimal formed negative",
        "sample_policy": "uniform random plus channel/luma extrema",
        "sources": {},
    }
    try:
        for source_index, source in enumerate(args.source):
            label = source.stem.rsplit("_", 1)[-1]
            if label not in DEFAULT_FRAMES:
                raise ValueError(f"no frozen frame for {label}")
            frame_number = DEFAULT_FRAMES[label]
            with ProResRawDecoder(
                args.decoder, source, frame_number, 1
            ) as decoder:
                absolute_frame, raw = next(iter(decoder))
            formed_started = time.perf_counter()
            negative = engine.form_negative(raw, absolute_frame)
            formed_seconds = time.perf_counter() - formed_started
            report["sources"][label] = {
                "source": str(source),
                "absolute_frame": int(absolute_frame),
                "formed_negative_seconds": formed_seconds,
                "mean": audit_density(
                    model,
                    negative.mean_record_density,
                    args.sample_count,
                    4600 + source_index * 10,
                ),
                "formed": audit_density(
                    model,
                    negative.formed_record_density,
                    args.sample_count,
                    4601 + source_index * 10,
                ),
            }
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n")
            print(f"completed {label}", flush=True)
    finally:
        engine.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
