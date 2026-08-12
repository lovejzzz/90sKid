#!/usr/bin/env python3
"""Build lossless neutral probes for Silver Efex black-box measurement."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import cv2


def build(width: int, height: int) -> np.ndarray:
    image = np.zeros((height, width, 3), dtype=np.uint16)
    half = height // 2
    ramp = np.linspace(0, 65535, width, dtype=np.uint16)
    image[:half] = ramp[None, :, None]
    levels = np.linspace(0.025, 0.975, 16)
    edges = np.linspace(0, width, len(levels) + 1, dtype=int)
    for index, level in enumerate(levels):
        code = np.uint16(round(float(level) * 65535.0))
        image[half:, edges[index] : edges[index + 1]] = code
    # Thin hard edges and a Siemens-like radial wedge provide edge/NPS evidence
    # without disturbing the large flat measurement interiors.
    y0, y1 = half - 64, half
    image[y0:y1, : width // 2] = 0
    image[y0:y1, width // 2 :] = 65535
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--width", type=int, default=2048)
    parser.add_argument("--height", type=int, default=2048)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(
        str(args.output),
        build(args.width, args.height)[..., ::-1],
        [cv2.IMWRITE_TIFF_COMPRESSION, 1],
    ):
        raise RuntimeError(f"could not write {args.output}")
    print(args.output.resolve())


if __name__ == "__main__":
    main()
