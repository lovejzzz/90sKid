#!/usr/bin/env python3
"""Prepare a native RGB float fixture and exact OpenCV separable-blur reference."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sigma", type=float, default=3.1)
    parser.add_argument("--radius", type=int, default=12)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = np.asarray(np.load(args.input, mmap_mode="r"), dtype=np.float32)
    kernel = cv2.getGaussianKernel(
        2 * args.radius + 1, args.sigma, cv2.CV_32F
    ).reshape(-1)
    started = time.perf_counter()
    reference = cv2.sepFilter2D(
        source,
        -1,
        kernel,
        kernel,
        borderType=cv2.BORDER_REFLECT,
    )
    seconds = time.perf_counter() - started
    source.tofile(args.output / "input_rgb_f32.raw")
    kernel.astype(np.float32).tofile(args.output / "weights_f32.raw")
    reference.tofile(args.output / "opencv_reference_rgb_f32.raw")
    metadata = {
        "shape": list(source.shape),
        "sigma": args.sigma,
        "radius": args.radius,
        "kernel_size": int(kernel.size),
        "opencv_seconds": seconds,
    }
    (args.output / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
