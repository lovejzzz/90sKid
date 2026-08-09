#!/usr/bin/env python3
"""Compare two grain realizations in formed-negative density statistics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


FREQUENCY_EDGES = np.array([0.0, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.72])


def moment_summary(residual: np.ndarray) -> dict[str, object]:
    flat = residual.reshape(-1, 3).astype(np.float64)
    mean = flat.mean(axis=0)
    centered = flat - mean
    variance = np.mean(centered * centered, axis=0)
    std = np.sqrt(variance)
    skew = np.mean(centered**3, axis=0) / np.maximum(std**3, 1e-30)
    kurtosis = np.mean(centered**4, axis=0) / np.maximum(variance**2, 1e-30) - 3.0
    covariance = centered.T @ centered / flat.shape[0]
    correlation = covariance / np.maximum(np.outer(std, std), 1e-30)
    return {
        "mean": mean.tolist(),
        "std": std.tolist(),
        "skew": skew.tolist(),
        "excess_kurtosis": kurtosis.tolist(),
        "correlation": correlation.tolist(),
    }


def welch_radial_bands(residual: np.ndarray, tile: int = 512) -> dict[str, object]:
    height, width, _ = residual.shape
    ys = np.linspace(0, height - tile, 4, dtype=int)
    xs = np.linspace(0, width - tile, 5, dtype=int)
    window_1d = np.hanning(tile).astype(np.float32)
    window = window_1d[:, None] * window_1d[None, :]
    fy = np.fft.fftfreq(tile)[:, None]
    fx = np.fft.rfftfreq(tile)[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    band_masks = [
        (radius >= FREQUENCY_EDGES[index])
        & (radius < FREQUENCY_EDGES[index + 1])
        for index in range(len(FREQUENCY_EDGES) - 1)
    ]
    powers = np.zeros((3, len(band_masks)), dtype=np.float64)
    counts = np.zeros(len(band_masks), dtype=np.int64)
    for y in ys:
        for x in xs:
            patch = residual[y : y + tile, x : x + tile]
            patch = patch - patch.mean(axis=(0, 1), keepdims=True)
            for channel in range(3):
                spectrum = np.fft.rfft2(patch[..., channel] * window)
                power = np.abs(spectrum) ** 2
                for band, mask in enumerate(band_masks):
                    powers[channel, band] += power[mask].mean()
            counts += 1
    powers /= counts[None, :]
    normalized = powers / np.maximum(powers.sum(axis=1, keepdims=True), 1e-30)
    labels = [
        f"{FREQUENCY_EDGES[i]:.2f}-{FREQUENCY_EDGES[i + 1]:.2f}"
        for i in range(len(FREQUENCY_EDGES) - 1)
    ]
    return {
        "frequency_bands_cycles_per_pixel": labels,
        "power": powers.tolist(),
        "normalized_power": normalized.tolist(),
        "tile_count": int(len(ys) * len(xs)),
    }


def load_residual(root: Path) -> np.ndarray:
    mean = np.load(root / "mean_density.npy", mmap_mode="r")
    formed = np.load(root / "formed_density.npy", mmap_mode="r")
    return np.asarray(formed - mean, dtype=np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    reference = load_residual(args.reference)
    candidate = load_residual(args.candidate)
    result = {
        "reference": {
            "moments": moment_summary(reference),
            "nps": welch_radial_bands(reference),
        },
        "candidate": {
            "moments": moment_summary(candidate),
            "nps": welch_radial_bands(candidate),
        },
    }
    ref_std = np.array(result["reference"]["moments"]["std"])
    can_std = np.array(result["candidate"]["moments"]["std"])
    ref_nps = np.array(result["reference"]["nps"]["normalized_power"])
    can_nps = np.array(result["candidate"]["nps"]["normalized_power"])
    result["comparison"] = {
        "std_ratio_candidate_over_reference": (can_std / ref_std).tolist(),
        "maximum_absolute_normalized_nps_band_delta": float(
            np.max(np.abs(can_nps - ref_nps))
        ),
        "rms_residual_difference": np.sqrt(
            np.mean((candidate.astype(np.float64) - reference) ** 2, axis=(0, 1))
        ).tolist(),
    }
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
