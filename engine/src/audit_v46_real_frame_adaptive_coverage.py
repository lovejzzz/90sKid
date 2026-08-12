#!/usr/bin/env python3
"""Count demand-loaded V46 spectral microbricks on a real formed negative."""

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
from v46_adaptive_spectral import demanded_microbrick_cells


def risk_cells(mask):
    shape = tuple(value - 1 for value in mask.shape)
    risk = np.zeros(shape, dtype=bool)
    first = mask[:-1, :-1, :-1]
    for red in (0, 1):
        for green in (0, 1):
            for blue in (0, 1):
                risk |= mask[
                    red : red + shape[0],
                    green : green + shape[1],
                    blue : blue + shape[2],
                ] != first
    return risk


def unique_cells(density, dmin, axis):
    flat = np.maximum(
        np.asarray(density, dtype=np.float32).reshape(-1, 3) - dmin, 0.0
    )
    chunks = []
    for start in range(0, flat.shape[0], 1_000_000):
        stop = min(start + 1_000_000, flat.shape[0])
        lower = np.searchsorted(axis, flat[start:stop], side="right") - 1
        lower = np.clip(lower, 0, axis.size - 2).astype(np.uint16)
        encoded = (
            lower[:, 0].astype(np.uint32) * (axis.size - 1) ** 2
            + lower[:, 1].astype(np.uint32) * (axis.size - 1)
            + lower[:, 2].astype(np.uint32)
        )
        chunks.append(np.unique(encoded))
    encoded = np.unique(np.concatenate(chunks))
    red = encoded // ((axis.size - 1) ** 2)
    remainder = encoded % ((axis.size - 1) ** 2)
    green = remainder // (axis.size - 1)
    blue = remainder % (axis.size - 1)
    return np.stack([red, green, blue], axis=1).astype(np.int16)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--frame", type=int, required=True)
    parser.add_argument("--printer", type=Path, required=True)
    parser.add_argument("--residual", type=Path, required=True)
    parser.add_argument("--axis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cells-output", type=Path)
    parser.add_argument("--mtf-stages-only", action="store_true")
    args = parser.parse_args()
    engine = Emulsion5279Engine(
        EngineConfig(
            profile="v72",
            mode=EngineMode.PRODUCTION_METAL,
            observer_branch_workers=1,
        )
    )
    engine.configure()
    model = legacy.model
    model.GRAIN_STOCHASTIC_EXPOSURE_POLICY = (
        "full_stochastic_state_endpoint_hold"
    )
    try:
        with ProResRawDecoder(args.decoder, args.source, args.frame, 1) as decoder:
            absolute_frame, raw = next(iter(decoder))
        started = time.perf_counter()
        negative = engine.form_negative(raw, absolute_frame)
        formation_seconds = time.perf_counter() - started
        axis = np.load(args.axis).astype(np.float64)
        residual = np.load(args.residual, mmap_mode="r")
        node_mask = np.argmin(residual, axis=0).astype(np.uint8)
        risk = risk_cells(node_mask)
        printer = np.load(args.printer, mmap_mode="r")
        combined = np.take_along_axis(
            np.asarray(printer), node_mask[None, ..., None], axis=0
        )[0]
        dmin = np.asarray(model.SENSITO_DMIN_RGB, dtype=np.float32)
        mean_net = np.maximum(negative.mean_record_density - dmin, 0.0)
        formed_net = np.maximum(negative.formed_record_density - dmin, 0.0)
        mtf_mean_density = model.apply_5279_mtf_to_record_density(
            negative.mean_record_density, 1.0
        )
        mtf_formed_density = (
            mtf_mean_density
            + negative.formed_record_density
            - negative.mean_record_density
        ).astype(np.float32)
        mtf_mean_net = np.maximum(mtf_mean_density - dmin, 0.0)
        mtf_formed_net = np.maximum(mtf_formed_density - dmin, 0.0)
        mean_cells = unique_cells(negative.mean_record_density, dmin, axis)
        formed_cells = unique_cells(negative.formed_record_density, dmin, axis)
        union = np.unique(np.concatenate([mean_cells, formed_cells]), axis=0)
        active_risk = risk[union[:, 0], union[:, 1], union[:, 2]]
        if args.mtf_stages_only:
            mean_demand = demanded_microbrick_cells(
                combined, risk, axis, mtf_mean_net
            )
            formed_demand = demanded_microbrick_cells(
                combined, risk, axis, mtf_formed_net
            )
            discovery_stage = "post_5279_mtf_mean_and_formed"
        else:
            mean_demand = demanded_microbrick_cells(
                combined, risk, axis, mean_net
            )
            formed_demand = demanded_microbrick_cells(
                combined, risk, axis, formed_net
            )
            discovery_stage = "pre_5279_mtf_mean_and_formed"
        flagged = np.unique(
            np.concatenate([mean_demand, formed_demand]), axis=0
        )
        cells_sha256 = None
        if args.cells_output is not None:
            args.cells_output.parent.mkdir(parents=True, exist_ok=True)
            np.save(args.cells_output, flagged.astype(np.uint16))
            cells_sha256 = hashlib.sha256(
                args.cells_output.read_bytes()
            ).hexdigest()
        report = {
            "audit": "V46 real-frame demand-loaded spectral microbrick coverage",
            "source": str(args.source),
            "absolute_frame": int(absolute_frame),
            "negative_formation_seconds": formation_seconds,
            "base_atlas_size": int(axis.size),
            "mean_unique_parent_cells": int(mean_cells.shape[0]),
            "formed_unique_parent_cells": int(formed_cells.shape[0]),
            "union_unique_parent_cells": int(union.shape[0]),
            "active_set_risk_parent_cells": int(np.count_nonzero(active_risk)),
            "mean_runtime_demanded_microbrick_count": int(mean_demand.shape[0]),
            "formed_runtime_demanded_microbrick_count": int(
                formed_demand.shape[0]
            ),
            "demand_loaded_microbrick_count": int(flagged.shape[0]),
            "demand_loaded_cells_path": (
                str(args.cells_output) if args.cells_output is not None else None
            ),
            "demand_loaded_cells_sha256": cells_sha256,
            "microbrick_exact_nodes_with_duplicates_at_5_cubed": int(
                flagged.shape[0] * 125
            ),
            "discovery_policy": (
                "every real pixel evaluated by the same active-boundary OR "
                "linear-cubic disagreement predicate used at runtime"
            ),
            "discovery_stage": discovery_stage,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        engine.close()


if __name__ == "__main__":
    main()
