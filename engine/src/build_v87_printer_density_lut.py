#!/usr/bin/env python3
"""Build a dense V87 Status-M-to-2383 printer-density lattice.

The historical runtime lattice is only 29 cubed.  Building the exact joint
spectral inverse as one 193-cube allocation would create very large temporary
arrays, so this builder evaluates complete red-axis slabs and writes them to a
NumPy memmap.  Each cell still comes from the same V61 joint Status-M solve and
the same 3200 K / 2383 spectral integration; only cache precision changes.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import time

import numpy as np

import emulsion_experiment as e
import v72_profile


def exact_printer_density(status_m_net_density: np.ndarray) -> np.ndarray:
    """Evaluate the joint spectral printer-density map without a runtime LUT."""
    source = np.asarray(status_m_net_density, dtype=np.float64)
    original_shape = source.shape
    flat = source.reshape(-1, 3)
    cmy = e.solve_5279_analytical_cmy_from_status_m_net_density(flat)
    spectra = np.asarray(
        e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float64
    )
    lamp = np.asarray(
        e._blackbody_spd(e.NEGATIVE_DYE_WAVELENGTHS_NM, 3200.0),
        dtype=np.float64,
    )
    sensitivity = np.power(
        10.0, np.asarray(e.PRINT_2383_LOG_SENSITIVITY_CMY, dtype=np.float64)
    )
    weights = lamp[:, None] * sensitivity
    weights /= np.sum(weights, axis=0, keepdims=True)
    spectral_density = (
        np.asarray(e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY, dtype=np.float64)[
            None, :
        ]
        + np.asarray(cmy, dtype=np.float64) @ spectra.T
    )
    transmission = np.power(10.0, -np.clip(spectral_density, 0.0, 16.0))
    result = -np.log10(np.maximum(transmission @ weights, 1e-12))
    return result.reshape(original_shape).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, default=193)
    parser.add_argument("--slabs-per-flush", type=int, default=4)
    args = parser.parse_args()
    if args.size < 2:
        raise ValueError("size must be at least 2")

    v72_profile.apply(e)
    axis = np.linspace(
        0.0,
        e.NEGATIVE_5279_MAX_RECORD_DENSITY,
        args.size,
        dtype=np.float32,
    )
    green, blue = np.meshgrid(axis, axis, indexing="ij")
    temporary = args.output.with_suffix(args.output.suffix + ".partial")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    if temporary.exists():
        temporary.unlink()
    lattice = np.lib.format.open_memmap(
        temporary,
        mode="w+",
        dtype=np.float32,
        shape=(args.size, args.size, args.size, 3),
    )

    started = time.perf_counter()
    for red_index, red_value in enumerate(axis):
        red = np.full_like(green, red_value)
        targets = np.stack([red, green, blue], axis=-1)
        lattice[red_index] = exact_printer_density(targets)
        if (
            (red_index + 1) % args.slabs_per_flush == 0
            or red_index + 1 == args.size
        ):
            lattice.flush()
        elapsed = time.perf_counter() - started
        rate = (red_index + 1) / max(elapsed, 1e-9)
        remaining = (args.size - red_index - 1) / max(rate, 1e-9)
        print(
            f"slab {red_index + 1:03d}/{args.size} "
            f"elapsed={elapsed:.1f}s eta={remaining:.1f}s",
            flush=True,
        )

    del lattice
    os.replace(temporary, args.output)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    elapsed = time.perf_counter() - started
    print(
        f"sha256={digest} size={args.size} elapsed={elapsed:.3f}s "
        f"bytes={args.output.stat().st_size}",
        flush=True,
    )


if __name__ == "__main__":
    main()
