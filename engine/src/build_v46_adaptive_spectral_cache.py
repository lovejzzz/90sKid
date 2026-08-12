#!/usr/bin/env python3
"""Build the collapsed V46 base atlas and/or footage-demanded microbricks."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v72_profile
from v46_adaptive_spectral import collapse_base_atlas, build_microbrick_cache


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    base = subparsers.add_parser("base")
    base.add_argument("printer", type=Path)
    base.add_argument("residual", type=Path)
    base.add_argument("axis", type=Path)
    base.add_argument("output_prefix", type=Path)
    bricks = subparsers.add_parser("microbricks")
    bricks.add_argument("node_mask", type=Path)
    bricks.add_argument("axis", type=Path)
    bricks.add_argument("output_prefix", type=Path)
    bricks.add_argument("cells", nargs="+", type=Path)
    bricks.add_argument("--iterations", type=int, default=6)
    merge = subparsers.add_parser("merge")
    merge.add_argument("base_cells", type=Path)
    merge.add_argument("base_blocks", type=Path)
    merge.add_argument("delta_cells", type=Path)
    merge.add_argument("delta_blocks", type=Path)
    merge.add_argument("output_prefix", type=Path)
    args = parser.parse_args()

    if args.command == "base":
        report = collapse_base_atlas(
            args.printer, args.residual, args.axis, args.output_prefix
        )
    elif args.command == "microbricks":
        v72_profile.apply(e)
        cells = np.unique(
            np.concatenate([np.load(path) for path in args.cells]), axis=0
        )
        report = build_microbrick_cache(
            e,
            cells,
            args.node_mask,
            args.axis,
            args.output_prefix,
            iterations=args.iterations,
        )
    else:
        base_cells = np.load(args.base_cells)
        base_blocks = np.load(args.base_blocks, mmap_mode="r")
        delta_cells = np.load(args.delta_cells)
        delta_blocks = np.load(args.delta_blocks, mmap_mode="r")
        cells = np.concatenate([base_cells, delta_cells]).astype(np.int16)
        blocks = np.concatenate([base_blocks, delta_blocks]).astype(np.float32)
        codes = (cells[:, 0].astype(np.int64) * 128 + cells[:, 1]) * 128 + cells[:, 2]
        if np.unique(codes).size != codes.size:
            raise ValueError("base and delta microbrick caches overlap")
        order = np.argsort(codes)
        cells = cells[order]
        blocks = blocks[order]
        cells_path = args.output_prefix.with_name(
            args.output_prefix.name + "_cells.npy"
        )
        blocks_path = args.output_prefix.with_name(
            args.output_prefix.name + "_blocks.npy"
        )
        args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
        np.save(cells_path, cells)
        np.save(blocks_path, blocks)
        report = {
            "policy": "sorted_nonoverlapping_microbrick_cache_merge",
            "base_cell_count": int(base_cells.shape[0]),
            "delta_cell_count": int(delta_cells.shape[0]),
            "merged_cell_count": int(cells.shape[0]),
            "assets": {
                "cells": {
                    "path": str(cells_path),
                    "sha256": hashlib.sha256(cells_path.read_bytes()).hexdigest(),
                },
                "blocks": {
                    "path": str(blocks_path),
                    "sha256": hashlib.sha256(blocks_path.read_bytes()).hexdigest(),
                },
            },
        }
        args.output_prefix.with_name(
            args.output_prefix.name + "_merge.json"
        ).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
