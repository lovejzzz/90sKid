#!/usr/bin/env python3
"""Gate the adaptive V46 observer against exact NNLS on real negatives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from emulsion5279 import legacy
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import ProResRawDecoder
from emulsion5279.pipeline import Emulsion5279Engine
from audit_v46_real_frame_nnls import DEFAULT_FRAMES, sample_indices
from v46_adaptive_spectral import AdaptivePrinterDensityObserver
from v46_status_m_active_set import printer_density_from_cmy, solve_nnls


def metrics(approximate: np.ndarray, exact: np.ndarray) -> dict[str, object]:
    error = np.asarray(approximate, np.float64) - np.asarray(exact, np.float64)
    absolute = np.abs(error)
    worst = np.unravel_index(np.argmax(absolute), absolute.shape)
    maximum = float(absolute[worst])
    return {
        "maximum_absolute_printer_density_error": maximum,
        "p99_absolute_printer_density_error": float(
            np.percentile(absolute, 99)
        ),
        "rms_printer_density_error": float(
            np.sqrt(np.mean(np.square(error)))
        ),
        "worst_sample_index": int(worst[0]),
        "worst_output_record": ("red", "green", "blue")[worst[1]],
        "quality_gate_maximum_density_error": 0.001,
        "quality_gate_pass": maximum < 0.001,
    }


def audit_density(
    model,
    observer: AdaptivePrinterDensityObserver,
    density: np.ndarray,
    count: int,
    seed: int,
) -> dict[str, object]:
    flat = np.asarray(density, dtype=np.float32).reshape(-1, 3)
    indices = sample_indices(density, count, seed)
    target = np.maximum(
        flat[indices] - np.asarray(model.SENSITO_DMIN_RGB, np.float32), 0.0
    )
    approximate_started = time.perf_counter()
    approximate = observer.sample(target)
    approximate_seconds = time.perf_counter() - approximate_started
    exact_started = time.perf_counter()
    cmy, masks, _ = solve_nnls(model, target, iterations=24)
    exact = printer_density_from_cmy(model, cmy)
    exact_seconds = time.perf_counter() - exact_started
    return {
        "sample_count": int(target.shape[0]),
        "adaptive_seconds": approximate_seconds,
        "exact_seconds": exact_seconds,
        "active_mask_counts": {
            str(int(mask)): int(number)
            for mask, number in zip(
                *np.unique(masks, return_counts=True), strict=True
            )
        },
        **metrics(approximate, exact),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--source", action="append", type=Path, required=True)
    parser.add_argument("--sample-count", type=int, default=6_000)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    observer = AdaptivePrinterDensityObserver(
        args.prefix.with_name(args.prefix.name + "_base.npy"),
        args.prefix.with_name(args.prefix.name + "_active_risk.npy"),
        args.prefix.with_name(args.prefix.name + "_axis.npy"),
        args.prefix.with_name(args.prefix.name + "_cells.npy"),
        args.prefix.with_name(args.prefix.name + "_blocks.npy"),
    )
    config = EngineConfig(
        profile="v72",
        mode=EngineMode.PRODUCTION_METAL,
        observer_branch_workers=1,
    )
    model = legacy.model
    report: dict[str, object] = {
        "audit": "V46 adaptive observer exact real-frame precision gate",
        "profile": "V72 plus complete stochastic endpoint hold",
        "sources": {},
    }
    for source_index, source in enumerate(args.source):
        # Each source is a separate camera take and may legitimately begin at
        # absolute frame zero.  A fresh sampler session preserves the duplicate
        # identity guard within a take without falsely joining independent clips.
        engine = Emulsion5279Engine(config)
        engine.configure()
        model.GRAIN_STOCHASTIC_EXPOSURE_POLICY = (
            "full_stochastic_state_endpoint_hold"
        )
        try:
            label = source.stem.rsplit("_", 1)[-1]
            frame_number = DEFAULT_FRAMES[label]
            with ProResRawDecoder(
                args.decoder, source, frame_number, 1
            ) as decoder:
                absolute_frame, raw = next(iter(decoder))
            formed_started = time.perf_counter()
            negative = engine.form_negative(raw, absolute_frame)
            row = {
                "source": str(source),
                "absolute_frame": int(absolute_frame),
                "negative_formation_seconds": float(
                    time.perf_counter() - formed_started
                ),
                "mean": audit_density(
                    model,
                    observer,
                    negative.mean_record_density,
                    args.sample_count,
                    4640 + source_index * 10,
                ),
                "formed": audit_density(
                    model,
                    observer,
                    negative.formed_record_density,
                    args.sample_count,
                    4641 + source_index * 10,
                ),
            }
            report["sources"][label] = row
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2) + "\n")
            print(f"completed {label}", flush=True)
        finally:
            engine.close()
    gates = [
        branch["quality_gate_pass"]
        for row in report["sources"].values()
        for branch in (row["mean"], row["formed"])
    ]
    report["all_quality_gates_pass"] = bool(all(gates))
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
