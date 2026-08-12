#!/usr/bin/env python3
"""Build branch printer-density and residual cubes for the V46 NNLS inverse."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

import emulsion_experiment as e
import v72_profile
from v46_status_m_active_set import printer_density_from_cmy, solve_active_set


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prefix", type=Path)
    parser.add_argument("--size", type=int, default=65)
    parser.add_argument("--iterations", type=int, default=24)
    parser.add_argument("--axis-power", type=float, default=1.0)
    args = parser.parse_args()
    if args.size < 2:
        raise ValueError("size must be at least two")
    if args.axis_power <= 0.0:
        raise ValueError("axis power must be positive")
    v72_profile.apply(e)
    axis = e.NEGATIVE_5279_MAX_RECORD_DENSITY * np.power(
        np.linspace(0.0, 1.0, args.size, dtype=np.float64),
        args.axis_power,
    )
    red, green, blue = np.meshgrid(axis, axis, axis, indexing="ij")
    targets = np.stack([red, green, blue], axis=-1).reshape(-1, 3)
    printer = np.empty((8, args.size, args.size, args.size, 3), np.float32)
    residual = np.empty((8, args.size, args.size, args.size), np.float32)
    started = time.perf_counter()
    branch_seconds: dict[str, float] = {}
    for mask in range(8):
        branch_started = time.perf_counter()
        coefficients, squared_error = solve_active_set(
            e, targets, mask, iterations=args.iterations
        )
        printer[mask] = printer_density_from_cmy(e, coefficients).reshape(
            args.size, args.size, args.size, 3
        )
        residual[mask] = squared_error.reshape(args.size, args.size, args.size)
        branch_seconds[str(mask)] = time.perf_counter() - branch_started
        print(
            f"active-set {mask}/7 elapsed={branch_seconds[str(mask)]:.3f}s",
            flush=True,
        )
    if not np.isfinite(printer).all() or not np.isfinite(residual).all():
        raise FloatingPointError("active-set cube contains non-finite data")
    printer_path = args.prefix.with_name(args.prefix.name + "_printer.npy")
    residual_path = args.prefix.with_name(args.prefix.name + "_residual.npy")
    report_path = args.prefix.with_name(args.prefix.name + "_build.json")
    axis_path = args.prefix.with_name(args.prefix.name + "_axis.npy")
    printer_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(printer_path, printer)
    np.save(residual_path, residual)
    np.save(axis_path, axis.astype(np.float32))
    report = {
        "policy": "eight_active_set_nonnegative_status_m_inverse",
        "size": args.size,
        "iterations": args.iterations,
        "axis_power": args.axis_power,
        "elapsed_seconds": time.perf_counter() - started,
        "branch_seconds": branch_seconds,
        "printer_path": str(printer_path),
        "printer_sha256": digest(printer_path),
        "residual_path": str(residual_path),
        "residual_sha256": digest(residual_path),
        "axis_path": str(axis_path),
        "axis_sha256": digest(axis_path),
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
