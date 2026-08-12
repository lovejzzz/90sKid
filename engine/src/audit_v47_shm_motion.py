#!/usr/bin/env python3
"""Temporal gates for the SHM stochastic organization independent of scene motion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from shm_density import morphology_latent_field


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--width", type=int, default=1024)
    args = parser.parse_args()
    fields = [
        morphology_latent_field(args.height, args.width, frame, tone=0.50)
        for frame in range(args.frames)
    ]
    correlations: list[float] = []
    difference_ratios: list[float] = []
    phase_peaks: list[float] = []
    for first, second in zip(fields, fields[1:]):
        correlations.append(float(np.corrcoef(first.ravel(), second.ravel())[0, 1]))
        difference_ratios.append(
            float(np.std(second - first) / np.sqrt(np.var(first) + np.var(second)))
        )
        # A translated fixed plate creates a sharp phase-correlation peak even
        # if its zero-lag correlation is low. Independent film realizations do not.
        product = np.fft.rfft2(first) * np.conj(np.fft.rfft2(second))
        product /= np.maximum(np.abs(product), 1.0e-12)
        phase = np.fft.irfft2(product, s=first.shape)
        phase_peaks.append(float(np.max(np.abs(phase))))
    gates = {
        "adjacent_zero_lag_independent": max(abs(x) for x in correlations) < 0.01,
        "independent_difference_rms": max(abs(x - 1.0) for x in difference_ratios) < 0.01,
        "no_translated_fixed_plate": max(phase_peaks) < 0.01,
    }
    report = {
        "audit": "V47 SHM temporal morphology",
        "frames": args.frames,
        "dimensions": [args.width, args.height],
        "adjacent_correlation": correlations,
        "adjacent_independent_difference_rms_ratio": difference_ratios,
        "phase_correlation_peak": phase_peaks,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
        "boundary": (
            "independent renewal is a conservative motion-film hypothesis; "
            "Silver Efex is a still-image product and cannot identify temporal grain"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_gates_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
