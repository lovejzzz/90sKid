#!/usr/bin/env python3
"""Audit V46 cache coverage at every negative-density observer entry point."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from emulsion5279 import legacy
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import ProResRawDecoder
from emulsion5279.pipeline import Emulsion5279Engine
from audit_v46_real_frame_nnls import DEFAULT_FRAMES
from v46_adaptive_spectral import AdaptivePrinterDensityObserver


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--source", action="append", type=Path, required=True)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cells-output", type=Path, required=True)
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
        "audit": "V46 pipeline-stage adaptive cache coverage",
        "sources": {},
    }
    all_missing: list[np.ndarray] = []
    for source in args.source:
        engine = Emulsion5279Engine(config)
        engine.configure()
        model.GRAIN_STOCHASTIC_EXPOSURE_POLICY = (
            "full_stochastic_state_endpoint_hold"
        )
        try:
            label = source.stem.rsplit("_", 1)[-1]
            with ProResRawDecoder(
                args.decoder, source, DEFAULT_FRAMES[label], 1
            ) as decoder:
                absolute_frame, raw = next(iter(decoder))
            started = time.perf_counter()
            negative = engine.form_negative(raw, absolute_frame)
            mtf_mean = model.apply_5279_mtf_to_record_density(
                negative.mean_record_density, 1.0
            )
            mtf_formed = (
                mtf_mean
                + negative.formed_record_density
                - negative.mean_record_density
            ).astype(np.float32)
            dmin = np.asarray(model.SENSITO_DMIN_RGB, np.float32)
            stage_missing = {
                "pre_mtf_mean": observer.missing_microbrick_cells(
                    np.maximum(negative.mean_record_density - dmin, 0.0)
                ),
                "pre_mtf_formed": observer.missing_microbrick_cells(
                    np.maximum(negative.formed_record_density - dmin, 0.0)
                ),
                "post_mtf_mean": observer.missing_microbrick_cells(
                    np.maximum(mtf_mean - dmin, 0.0)
                ),
                "post_mtf_formed": observer.missing_microbrick_cells(
                    np.maximum(mtf_formed - dmin, 0.0)
                ),
            }
            for cells in stage_missing.values():
                if cells.size:
                    all_missing.append(cells)
            report["sources"][label] = {
                "source": str(source),
                "absolute_frame": int(absolute_frame),
                "seconds": float(time.perf_counter() - started),
                "missing_cells_by_stage": {
                    name: int(cells.shape[0])
                    for name, cells in stage_missing.items()
                },
            }
            print(f"completed {label}", flush=True)
        finally:
            engine.close()
    union = (
        np.unique(np.concatenate(all_missing), axis=0)
        if all_missing
        else np.empty((0, 3), dtype=np.int16)
    )
    args.cells_output.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.cells_output, union)
    report["union_missing_cell_count"] = int(union.shape[0])
    report["cells_output"] = str(args.cells_output)
    report["cells_sha256"] = hashlib.sha256(
        args.cells_output.read_bytes()
    ).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
