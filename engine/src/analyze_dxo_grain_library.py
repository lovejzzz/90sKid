#!/usr/bin/env python3
"""Measure stock-specific morphology in extracted DxO grain-patch resources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def excess_kurtosis(values: np.ndarray) -> float:
    centered = values - values.mean()
    variance = float(np.mean(centered * centered))
    return float(np.mean(centered**4) / (variance * variance) - 3.0) if variance else 0.0


def skewness(values: np.ndarray) -> float:
    centered = values - values.mean()
    sigma = float(np.sqrt(np.mean(centered * centered)))
    return float(np.mean(centered**3) / sigma**3) if sigma else 0.0


def autocorrelation_samples(signal: np.ndarray) -> dict[str, float]:
    centered = signal - signal.mean()
    variance = float(np.mean(centered * centered))
    if variance == 0:
        return {"x1": 0.0, "x2": 0.0, "x4": 0.0, "y1": 0.0, "y2": 0.0, "y4": 0.0}

    def corr(dy: int, dx: int) -> float:
        a = centered[max(dy, 0) : centered.shape[0] + min(dy, 0), max(dx, 0) : centered.shape[1] + min(dx, 0)]
        b = centered[max(-dy, 0) : centered.shape[0] + min(-dy, 0), max(-dx, 0) : centered.shape[1] + min(-dx, 0)]
        return float(np.mean(a * b) / variance)

    return {"x1": corr(0, 1), "x2": corr(0, 2), "x4": corr(0, 4), "y1": corr(1, 0), "y2": corr(2, 0), "y4": corr(4, 0)}


def radial_power_bands(signal: np.ndarray) -> dict[str, float]:
    # Crop to 512² so every stock is compared on the same FFT grid.
    signal = signal[:512, :512] - signal[:512, :512].mean()
    spectrum = np.abs(np.fft.rfft2(signal)) ** 2
    fy = np.fft.fftfreq(signal.shape[0])[:, None]
    fx = np.fft.rfftfreq(signal.shape[1])[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    total = float(spectrum[radius > 0].sum())
    bands = {"low_0_003125": (0.0, 0.03125), "mid_003125_0125": (0.03125, 0.125), "high_0125_05": (0.125, 0.5)}
    return {
        name: float(spectrum[(radius > low) & (radius <= high)].sum() / total)
        for name, (low, high) in bands.items()
    }


def seam_metrics(signal: np.ndarray) -> dict[str, float]:
    return {
        "left_right_mean_abs": float(np.mean(np.abs(signal[:, 0] - signal[:, -1]))),
        "top_bottom_mean_abs": float(np.mean(np.abs(signal[0, :] - signal[-1, :]))),
        "ordinary_horizontal_neighbor_mean_abs": float(np.mean(np.abs(np.diff(signal, axis=1)))),
        "ordinary_vertical_neighbor_mean_abs": float(np.mean(np.abs(np.diff(signal, axis=0)))),
    }


def analyze_image(path: Path) -> dict[str, object]:
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    flat = rgb.reshape(-1, 3)
    luma = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return {
        "shape": list(rgb.shape),
        "channel_mean": flat.mean(axis=0).tolist(),
        "channel_std": flat.std(axis=0).tolist(),
        "channel_correlation": np.corrcoef(flat, rowvar=False).tolist(),
        "max_channel_range": float(np.max(np.ptp(rgb, axis=2))),
        "luma_mean": float(luma.mean()),
        "luma_std": float(luma.std()),
        "luma_skewness": skewness(luma),
        "luma_excess_kurtosis": excess_kurtosis(luma),
        "luma_autocorrelation": autocorrelation_samples(luma),
        "luma_radial_power_fraction": radial_power_bands(luma),
        "luma_seams": seam_metrics(luma),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("patch_directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    registry = json.loads(args.registry.resolve(strict=True).read_text())
    patch_directory = args.patch_directory.resolve(strict=True)
    records = []
    for record in registry["records"]:
        if not record["black_white"] or not record["archive_entry"]:
            continue
        path = patch_directory / record["archive_entry"]["filename"]
        records.append(
            {
                "name": record["name"],
                "resource_id": record["resource_id"],
                "archive_index": record["archive_entry"]["index"],
                "filename": path.name,
                "measurements": analyze_image(path),
            }
        )

    result = {
        "registry": str(args.registry.resolve()),
        "patch_directory": str(patch_directory),
        "count": len(records),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(records), "output": str(args.output.resolve())}, indent=2))


if __name__ == "__main__":
    main()
