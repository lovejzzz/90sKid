#!/usr/bin/env python3
"""Compare isolated opponent-colour impulses without penalizing real edges."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


LUMA = np.asarray([0.2126, 0.7152, 0.0722], np.float32)


def decode_frame(path: Path, frame: int) -> np.ndarray:
    command = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf",
        (
            f"select=eq(n\\,{frame}),"
            "setparams=color_primaries=bt709:"
            "color_trc=iec61966-2-1:colorspace=bt709"
        ),
        "-frames:v", "1", "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
    ]
    payload = subprocess.check_output(command)
    expected = 5760 * 4320 * 3 * 2
    if len(payload) != expected:
        raise RuntimeError(f"short frame {len(payload)}/{expected}: {path}")
    return (
        np.frombuffer(payload, "<u2")
        .reshape(4320, 5760, 3)
        .astype(np.float32)
        / 65535.0
    )


def measure(rgb: np.ndarray) -> dict[str, float | int]:
    median = cv2.medianBlur(rgb, 3)
    residual = rgb - median
    luma = np.einsum("...c,c->...", rgb, LUMA)
    luma_residual = np.einsum("...c,c->...", residual, LUMA)
    opponent = residual - luma_residual[..., None]
    magnitude = np.max(opponent, axis=2) - np.min(opponent, axis=2)
    dark = luma < 0.18
    dark_count = int(np.sum(dark))
    result: dict[str, float | int] = {
        "dark_pixels": dark_count,
        "median_opponent_p9999": float(np.quantile(magnitude[dark], 0.9999)),
    }
    for threshold in (0.04, 0.05, 0.06, 0.08):
        strong = dark & (magnitude > threshold)
        neighbor_count = cv2.boxFilter(
            strong.astype(np.uint8),
            ddepth=cv2.CV_16U,
            ksize=(3, 3),
            normalize=False,
            borderType=cv2.BORDER_CONSTANT,
        ) - strong.astype(np.uint16)
        isolated = strong & (neighbor_count == 0)
        key = str(threshold).replace(".", "_")
        result[f"all_gt_{key}_per_million"] = float(
            np.sum(strong) / dark_count * 1e6
        )
        result[f"isolated_gt_{key}_per_million"] = float(
            np.sum(isolated) / dark_count * 1e6
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--frame", type=int, default=0)
    args = parser.parse_args()
    report = {
        str(path): measure(decode_frame(path, args.frame))
        for path in args.paths
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
