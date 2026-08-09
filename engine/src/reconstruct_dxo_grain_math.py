#!/usr/bin/env python3
"""Executable reconstruction of confirmed Silver Efex lookup/mix mathematics.

This script does not call or modify Nik/DxO software.  It records the exact
integer uniform field and tone-taper equations reconstructed from the locally
installed ARM64 engine, then verifies their numerical invariants.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def uniform_lookup() -> np.ndarray:
    result = np.empty((256, 256), dtype=np.float32)
    # All hash instructions operate on ARM64 W registers: overflow is uint32.
    mask = (1 << 32) - 1
    for y in range(256):
        state = (y * 1025) & mask
        state ^= state >> 6
        state = (state * 1025) & mask
        for x in range(256):
            h = state ^ (state >> 6)
            h = (h * 9) & mask
            h ^= h >> 11
            h = (h * 32769) & mask
            result[y, x] = (h & 0xFFFF) / 65535.0
            state = (state + 1025) & mask
    return result


def tone_taper(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float64)
    low = ((((1811.956543 * y - 876.202087) * y + 117.616173) * y + 0.764699578) * y + 0.25)
    high = ((((1811.956543 * y - 6371.624023) * y + 8360.749023) * y - 4855.216797) * y + 1054.385376)
    return np.where(y < 0.2, low, np.where(y > 0.8, high, 1.0))


def mix_luma(y: np.ndarray, grain_candidate: np.ndarray, grain_strength: float) -> np.ndarray:
    alpha = grain_strength * tone_taper(y)
    return (1.0 - alpha) * y + alpha * grain_candidate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    lookup = uniform_lookup()
    tone_points = np.array([0, 0.05, 0.1, 0.15, 0.2, 0.5, 0.8, 0.85, 0.9, 0.95, 1.0])
    taper = tone_taper(tone_points)

    # The interpolation must be identity at zero strength and equal the grain
    # candidate when strength/taper are both one.
    probe_y = np.linspace(0.2, 0.8, 17)
    probe_g = probe_y[::-1]
    if not np.array_equal(mix_luma(probe_y, probe_g, 0.0), probe_y):
        raise AssertionError("zero-strength mix is not identity")
    if not np.allclose(mix_luma(probe_y, probe_g, 1.0), probe_g):
        raise AssertionError("unity midtone mix does not select grain candidate")

    result = {
        "uniform_lookup": {
            "shape": list(lookup.shape),
            "dtype": str(lookup.dtype),
            "sha256": hashlib.sha256(lookup.tobytes()).hexdigest(),
            "minimum": float(lookup.min()),
            "maximum": float(lookup.max()),
            "mean": float(lookup.mean()),
            "standard_deviation": float(lookup.std()),
            "unique_values": int(np.unique(lookup).size),
        },
        "tone_taper": [
            {"Y": float(y), "A": float(a)} for y, a in zip(tone_points, taper)
        ],
        "confirmed_density_mix": "Y' = (1 - grainStrength*A(Y))*Y + grainStrength*A(Y)*G",
        "confirmed_binomial_lookup": "G = inverse_CDF(Binomial(N,p),u)/N",
        "invariants": {
            "zero_strength_identity": True,
            "unity_midtone_selects_grain_candidate": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
