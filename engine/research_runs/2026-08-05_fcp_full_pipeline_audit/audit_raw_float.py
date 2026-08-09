#!/usr/bin/env python3
"""Measure one native AVFoundation extended-linear ProRes RAW frame."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frame", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    completed = subprocess.run(
        [str(args.decoder), str(args.input), str(args.frame), "1"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    expected = args.width * args.height * 3 * 4
    if len(completed.stdout) != expected:
        raise RuntimeError(f"decoded {len(completed.stdout)} bytes; expected {expected}")
    image = np.frombuffer(completed.stdout, dtype="<f4").reshape(
        args.height, args.width, 3
    )
    report = {
        "frame": args.frame,
        "shape": list(image.shape),
        "decoder_stderr": completed.stderr.decode("utf-8", errors="replace"),
        "all_finite": bool(np.all(np.isfinite(image))),
        "channel_min": np.min(image, axis=(0, 1)).tolist(),
        "channel_max": np.max(image, axis=(0, 1)).tolist(),
        "channel_quantiles": np.quantile(
            image, [0.0001, 0.001, 0.01, 0.5, 0.99, 0.999, 0.9999], axis=(0, 1)
        ).tolist(),
        "fraction_below_zero": np.mean(image < 0.0, axis=(0, 1)).tolist(),
        "fraction_above_one": np.mean(image > 1.0, axis=(0, 1)).tolist(),
        "fraction_exact_zero": np.mean(image == 0.0, axis=(0, 1)).tolist(),
        "fraction_exact_one": np.mean(image == 1.0, axis=(0, 1)).tolist(),
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
