#!/usr/bin/env python3
"""Isolate V45's observer change on one bit-identical realized V44 negative."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from engine.emulsion5279.assets import PRINT_2383_OUTPUT_LATTICE_V45
from engine.emulsion5279.contracts import EngineConfig, EngineMode
from engine.emulsion5279.io import ProResRawDecoder
from engine.emulsion5279.pipeline import Emulsion5279Engine
from engine.emulsion5279 import legacy

import v45_profile


def array_sha256(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).view(np.uint8)).hexdigest()


def delta_summary(a: np.ndarray, b: np.ndarray) -> dict[str, object]:
    delta = np.asarray(b, np.float64) - np.asarray(a, np.float64)
    return {
        "rms": float(np.sqrt(np.mean(delta * delta))),
        "maximum_absolute": float(np.max(np.abs(delta))),
        "mean_rgb": np.mean(delta, axis=(0, 1)).tolist(),
        "mean_absolute_rgb": np.mean(np.abs(delta), axis=(0, 1)).tolist(),
        "p999_absolute": float(np.quantile(np.abs(delta), 0.999)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    engine = Emulsion5279Engine(
        EngineConfig(profile="v44", mode=EngineMode.ARCHIVE_EXACT_CPU)
    )
    with ProResRawDecoder(args.decoder, args.input, args.frame, 1) as decoder:
        absolute_frame, raw = next(iter(decoder))
    negative = engine.form_negative(raw, absolute_frame)
    v44 = engine.observe(negative, absolute_frame)

    # Reobserve one already formed negative. No RAW, exposure, stochastic site,
    # DIR, MTF or scan quantity is recomputed under a different profile.
    v45_profile.apply(legacy.model)
    legacy.model._PRINT_2383_MONITOR_OUTPUT_LUT = np.load(
        PRINT_2383_OUTPUT_LATTICE_V45.path, allow_pickle=False
    )
    engine.profile = v45_profile
    v45 = engine.observe(negative, absolute_frame)

    report = {
        "contract": "one bit-identical realized negative; observer-only ablation",
        "absolute_frame": int(absolute_frame),
        "formed_negative_sha256": array_sha256(negative.formed_record_density),
        "v44": {
            "projection_sha256": array_sha256(v44.projection_linear_rec709),
            "scan_sha256": array_sha256(v44.scan_linear_rec709),
        },
        "v45": {
            "projection_sha256": array_sha256(v45.projection_linear_rec709),
            "scan_sha256": array_sha256(v45.scan_linear_rec709),
        },
        "projection_delta": delta_summary(
            v44.projection_linear_rec709, v45.projection_linear_rec709
        ),
        "scan_delta": delta_summary(
            v44.scan_linear_rec709, v45.scan_linear_rec709
        ),
    }
    report["scan_is_bit_exact"] = (
        report["v44"]["scan_sha256"] == report["v45"]["scan_sha256"]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["scan_is_bit_exact"]:
        raise SystemExit("V45 unexpectedly changed the frozen scan branch")


if __name__ == "__main__":
    main()
