#!/usr/bin/env python3
"""Measure a controlled Silver Efex flat-step export without redistributing it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None or image.dtype != np.uint16 or image.shape != (2048, 2048, 3):
        raise ValueError(f"expected 2048-square RGB uint16 TIFF: {path}")
    return image[..., 0].astype(np.float64) / 65535.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("processed", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = read(args.source)
    processed = read(args.processed)
    rows: list[dict[str, float | int]] = []
    for index in range(16):
        x0 = index * 128 + 16
        x1 = (index + 1) * 128 - 16
        original = source[1120:1950, x0:x1]
        residual = processed[1120:1950, x0:x1] - original
        residual -= residual.mean()
        variance = float(np.mean(residual * residual))
        x1_lag = float(
            np.mean(residual[:, :-1] * residual[:, 1:]) / variance
        )
        y1_lag = float(
            np.mean(residual[:-1] * residual[1:]) / variance
        )
        rows.append(
            {
                "patch": index,
                "source_signal": float(original.mean()),
                "residual_rms": float(np.sqrt(variance)),
                "lag1_x": x1_lag,
                "lag1_y": y1_lag,
                "lag1_mean": (x1_lag + y1_lag) * 0.5,
                "skew": float(np.mean(residual**3) / variance**1.5),
                "excess_kurtosis": float(
                    np.mean(residual**4) / variance**2 - 3.0
                ),
            }
        )
    report = {
        "audit": "controlled Nik 8 Silver Efex black-box flat fields",
        "application": "Nik 8 Silver Efex",
        "filter": "Film Grain (Branded)",
        "stock": "Kodak Tri-X 400",
        "controls": {"GrainIntensity": 100, "GrainSize": 1},
        "export": "uncompressed 16-bit TIFF",
        "source_sha256": sha256(args.source),
        "processed_sha256": sha256(args.processed),
        "flat_fields": rows,
        "boundary": (
            "JSON contains derived measurements only. The proprietary output "
            "TIFF and installed stock resource are not redistributed."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
