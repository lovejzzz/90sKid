#!/usr/bin/env python3
"""Reject isolated primary-colour tails in V40 review stills.

V39's release audit checked conditional means and marginal record RMS only.
Those are necessary but cannot constrain cross-record covariance, kurtosis or
the nonlinear visible tail.  This audit measures the actual delivered sRGB
observer image at native resolution and rejects the failure mode reported in
V39: sparse saturated opponent-colour impulses in dark regions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def measure(path: Path) -> dict[str, float | int | list[int]]:
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(path)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    residual = rgb - cv2.GaussianBlur(
        rgb, (0, 0), 1.0, borderType=cv2.BORDER_REFLECT
    )
    luma = np.einsum("...c,c->...", rgb, LUMA)
    luma_residual = np.einsum("...c,c->...", residual, LUMA)
    opponent = residual - luma_residual[..., None]
    opponent_range = np.max(opponent, axis=2) - np.min(opponent, axis=2)
    dark = luma < 0.18
    dark_tail = opponent_range[dark]
    chroma_rms = float(np.sqrt(np.mean(opponent * opponent)))
    luma_rms = float(np.sqrt(np.mean(luma_residual * luma_residual)))
    return {
        "shape_height_width": [int(rgb.shape[0]), int(rgb.shape[1])],
        "dark_pixel_count": int(np.sum(dark)),
        "dark_opponent_p999": float(np.quantile(dark_tail, 0.999)),
        "dark_opponent_p9999": float(np.quantile(dark_tail, 0.9999)),
        "dark_opponent_maximum": float(np.max(dark_tail)),
        "dark_spikes_gt_0_04_per_million": float(
            np.sum(dark & (opponent_range > 0.04)) / np.sum(dark) * 1e6
        ),
        "dark_spikes_gt_0_05_per_million": float(
            np.sum(dark & (opponent_range > 0.05)) / np.sum(dark) * 1e6
        ),
        "visible_chroma_to_luma_highpass_rms": chroma_rms
        / max(luma_rms, 1e-12),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    projection = measure(args.projection)
    scan = measure(args.scan)
    gates = {
        "projection_primary_tail": {
            "pass": projection["dark_spikes_gt_0_05_per_million"] <= 2.0,
            "maximum_per_million": 2.0,
        },
        "projection_tail_shape": {
            "pass": (
                projection["dark_opponent_p9999"] <= 0.035
                and projection["dark_spikes_gt_0_04_per_million"] <= 25.0
            ),
            "maximum_p9999": 0.035,
            "maximum_gt_0_04_per_million": 25.0,
        },
        "projection_opponent_energy": {
            "pass": projection["visible_chroma_to_luma_highpass_rms"] <= 0.20,
            "maximum_ratio": 0.20,
        },
        "scan_primary_tail": {
            "pass": scan["dark_spikes_gt_0_04_per_million"] <= 1.0,
            "maximum_per_million": 1.0,
        },
        "scan_opponent_energy": {
            "pass": scan["visible_chroma_to_luma_highpass_rms"] <= 0.65,
            "maximum_ratio": 0.65,
        },
    }
    report = {
        "audit": "V40 delivered colour-grain covariance and tail gate",
        "projection": projection,
        "scan": scan,
        "gates": gates,
        "all_gates_pass": all(bool(gate["pass"]) for gate in gates.values()),
    }
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if not report["all_gates_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
