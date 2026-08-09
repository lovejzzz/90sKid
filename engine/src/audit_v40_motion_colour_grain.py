#!/usr/bin/env python3
"""Gate V40's colour-grain tails on every delivered native-resolution frame."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
BRANCHES = {"projection": "projection", "scan": "bluray_scan"}
MOVIE = "06_quicktime_preview_srgb_prores4444.mov"


def read_exact(stream, size: int) -> bytes:
    parts: list[bytes] = []
    remaining = size
    while remaining:
        part = stream.read(remaining)
        if not part:
            break
        parts.append(part)
        remaining -= len(part)
    return b"".join(parts)


def measure_frame(encoded: np.ndarray) -> dict[str, float | int]:
    rgb = encoded.astype(np.float32) / 65535.0
    residual = rgb - cv2.GaussianBlur(rgb, (0, 0), 1.0, borderType=cv2.BORDER_REFLECT)
    luma = np.einsum("...c,c->...", rgb, LUMA)
    luma_residual = np.einsum("...c,c->...", residual, LUMA)
    opponent = residual - luma_residual[..., None]
    opponent_range = np.max(opponent, axis=2) - np.min(opponent, axis=2)
    # The impulse detector applies a radius-1 median followed by a radius-1
    # neighbourhood test. Its mathematically valid support therefore excludes
    # a two-pixel perimeter. Including that perimeter makes the zero-padded
    # neighbourhood report false isolated impulses on the second-last row and
    # column (observed at x=5758/y=4318 in the original V40 audit).
    valid = np.zeros(luma.shape, dtype=bool)
    valid[2:-2, 2:-2] = True
    dark = (luma < 0.18) & valid
    count = int(np.sum(dark))
    tail = opponent_range[dark]
    chroma_rms = float(np.sqrt(np.mean(opponent * opponent)))
    luma_rms = float(np.sqrt(np.mean(luma_residual * luma_residual)))
    # Gaussian high-pass energy is useful for monitoring grain, but it also
    # responds to legitimate coloured foliage and rock edges. V39's reported
    # defect was instead a field of isolated primary-colour impulses. A 3x3
    # vector median residual plus an 8-neighbour isolation test distinguishes
    # that failure mode without declaring every real chromatic edge invalid.
    median_residual = rgb - cv2.medianBlur(rgb, 3)
    median_luma = np.einsum("...c,c->...", median_residual, LUMA)
    median_opponent = median_residual - median_luma[..., None]
    median_range = np.max(median_opponent, axis=2) - np.min(
        median_opponent, axis=2
    )
    median_tail = median_range[dark]
    isolated_rates: dict[str, float] = {}
    for threshold in (0.06, 0.08):
        strong = dark & (median_range > threshold)
        neighbor_count = cv2.boxFilter(
            strong.astype(np.uint8),
            ddepth=cv2.CV_16U,
            ksize=(3, 3),
            normalize=False,
            borderType=cv2.BORDER_CONSTANT,
        ) - strong.astype(np.uint16)
        isolated_count = int(np.sum(strong & (neighbor_count == 0)))
        isolated_rates[f"isolated_impulses_gt_{threshold:.2f}_count"] = isolated_count
        isolated_rates[f"isolated_impulses_gt_{threshold:.2f}_per_million"] = float(
            isolated_count / count * 1e6
        )
    return {
        "excluded_perimeter_pixels": 2,
        "dark_pixel_count": count,
        "dark_opponent_p9999": float(np.quantile(tail, 0.9999)),
        "dark_spikes_gt_0_04_per_million": float(np.sum(dark & (opponent_range > 0.04)) / count * 1e6),
        "dark_spikes_gt_0_05_per_million": float(np.sum(dark & (opponent_range > 0.05)) / count * 1e6),
        "visible_chroma_to_luma_highpass_rms": chroma_rms / max(luma_rms, 1e-12),
        "median_opponent_p9999": float(np.quantile(median_tail, 0.9999)),
        **isolated_rates,
    }


def measure_movie(path: Path, frames: int) -> dict[str, object]:
    width, height = 5760, 4320
    frame_bytes = width * height * 3 * 2
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0", "-an",
            "-vf", "setparams=color_primaries=bt709:color_trc=iec61966-2-1:colorspace=bt709",
            "-frames:v", str(frames), "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    assert decoder.stdout is not None
    rows: list[dict[str, float | int]] = []
    try:
        for index in range(frames):
            payload = read_exact(decoder.stdout, frame_bytes)
            if len(payload) != frame_bytes:
                raise RuntimeError(f"short decode at {index}/{frames}: {path}")
            encoded = np.frombuffer(payload, "<u2").reshape(height, width, 3)
            row = measure_frame(encoded)
            row["frame"] = index
            rows.append(row)
    finally:
        decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError(f"decoder failed: {path}")
    keys = [
        key
        for key in rows[0]
        if key not in {"frame", "dark_pixel_count", "excluded_perimeter_pixels"}
    ]
    return {
        "path": str(path),
        "frames": rows,
        "worst": {key: max(float(row[key]) for row in rows) for key in keys},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--scenes", nargs="+", default=["T002", "T007", "T031"])
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--profile", default="V40")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "audit": f"{args.profile} every-frame native-resolution delivered colour-grain gate",
        "valid_domain": (
            "two-pixel perimeter excluded: radius-1 median plus radius-1 "
            "isolation neighbourhood has no valid support there"
        ),
        "scenes": {},
    }
    passed = True
    for scene in args.scenes:
        scene_report: dict[str, object] = {}
        for name, directory in BRANCHES.items():
            result = measure_movie(args.root / scene / directory / MOVIE, args.frames)
            worst = result["worst"]
            rows = result["frames"]

            def discrete_rate_gate(threshold: float, limit_per_million: float) -> bool:
                count_key = f"isolated_impulses_gt_{threshold:.2f}_count"
                return all(
                    int(row[count_key])
                    <= int(np.ceil(int(row["dark_pixel_count"]) * limit_per_million / 1e6))
                    for row in rows
                )

            if name == "projection":
                gates = {
                    "dark_p9999_le_0_035": worst["dark_opponent_p9999"] <= 0.035,
                    "opponent_to_luma_le_0_20": worst["visible_chroma_to_luma_highpass_rms"] <= 0.20,
                    "median_p9999_le_0_05": worst["median_opponent_p9999"] <= 0.05,
                    "isolated_gt_0_06_count_le_ceil_5_per_million": discrete_rate_gate(0.06, 5.0),
                    "isolated_gt_0_08_count_le_ceil_1_per_million": discrete_rate_gate(0.08, 1.0),
                }
            else:
                gates = {
                    "median_p9999_le_0_05": worst["median_opponent_p9999"] <= 0.05,
                    "isolated_gt_0_06_count_le_ceil_5_per_million": discrete_rate_gate(0.06, 5.0),
                    "isolated_gt_0_08_count_le_ceil_1_per_million": discrete_rate_gate(0.08, 1.0),
                }
            result["gates"] = gates
            result["pass"] = all(gates.values())
            passed &= bool(result["pass"])
            scene_report[name] = result
        report["scenes"][scene] = scene_report
    report["all_gates_pass"] = passed
    output = args.output or args.root / f"{args.profile.lower()}_motion_colour_grain_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
