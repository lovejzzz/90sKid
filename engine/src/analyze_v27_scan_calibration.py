#!/usr/bin/env python3
"""Verify V27 scan gray balance without treating it as an artistic grade."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import emulsion_experiment as e
import v26_profile
import v27_profile


LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def finished_neutral_scale() -> tuple[np.ndarray, np.ndarray]:
    levels = np.concatenate(
        [
            np.zeros(1, dtype=np.float32),
            np.geomspace(1e-5, 10.0, 8192, dtype=np.float32),
        ]
    )
    neutral = np.repeat(levels[:, None], 3, axis=1)
    density = e.develop_5279_record_density(e.film_records_from_rgb(neutral))
    scanner = e.scanner_density_from_total_record_density(density)
    scan = e.render_cineon_scan_master_from_scanner_density(scanner)
    return levels, e.finish_cineon_scan_for_bluray(scan)


def stats(rgb: np.ndarray) -> dict[str, float]:
    luma = np.einsum("...c,c->...", rgb, LUMA)
    valid = (luma >= 0.005) & (luma <= 0.90)
    residual = np.max(np.abs(rgb[valid] - luma[valid, None]), axis=-1)
    green_opponent = rgb[valid, 1] - 0.5 * (
        rgb[valid, 0] + rgb[valid, 2]
    )
    return {
        "maximum_neutral_channel_residual": float(np.max(residual)),
        "p95_neutral_channel_residual": float(np.percentile(residual, 95)),
        "mean_neutral_channel_residual": float(np.mean(residual)),
        "maximum_absolute_green_opponent": float(np.max(np.abs(green_opponent))),
        "p95_absolute_green_opponent": float(
            np.percentile(np.abs(green_opponent), 95)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    v26_profile.apply(e)
    _, before = finished_neutral_scale()
    before_luma = np.einsum("...c,c->...", before, LUMA)

    v27_profile.apply(e)
    after = e.neutralize_spirit_finished_gray_scale(before)
    after_luma = np.einsum("...c,c->...", after, LUMA)

    # Reapplying V26 must restore the old branch; projection is independently
    # verified below on a deterministic density lattice.
    v26_profile.apply(e)
    density_axis = np.linspace(0.0, 2.8, 41, dtype=np.float32)
    c, m, y = np.meshgrid(density_axis, density_axis, density_axis, indexing="ij")
    density = np.stack([c, m, y], axis=-1) + e.SENSITO_DMIN_RGB
    projection_v26 = e.render_2383_monitor_projection_from_record_density(density)
    v27_profile.apply(e)
    projection_v27 = e.render_2383_monitor_projection_from_record_density(density)

    report = {
        "release": v27_profile.PROFILE["name"],
        "before": stats(before),
        "after": stats(after),
        "maximum_absolute_luma_drift": float(
            np.max(np.abs(after_luma - before_luma))
        ),
        "maximum_absolute_projection_drift": float(
            np.max(np.abs(projection_v27 - projection_v26))
        ),
        "constraints": {
            "negative": "V26 unchanged",
            "grain": "V26 unchanged; no new NPS inferred from hourly research",
            "dir_interimage": "V26 unchanged; no stock-specific coefficient inferred",
            "scanner_aperture": "V26 period 2K aperture unchanged",
            "black_gamma_luma": "per-pixel finished Rec.709 luminance preserved",
        },
    }
    (args.output / "v27_scan_calibration.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    valid = (before_luma >= 0.005) & (before_luma <= 0.90)
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.2))
    for channel, name, colour in zip(
        range(3), ("R", "G", "B"), ("#bd5a4d", "#5f8b64", "#4f719d")
    ):
        axes[0].plot(
            before_luma[valid],
            before[valid, channel] - before_luma[valid],
            label=name,
            color=colour,
            linewidth=1.7,
        )
        axes[1].plot(
            after_luma[valid],
            after[valid, channel] - after_luma[valid],
            label=name,
            color=colour,
            linewidth=1.7,
        )
    axes[0].set_title("V26 · two-anchor scan residual")
    axes[1].set_title("V27 · neutral-scale constrained")
    for axis in axes:
        axis.axhline(0.0, color="#222", linewidth=0.8)
        axis.set_xlabel("Display-linear Rec.709 luminance")
        axis.set_ylabel("Channel minus luminance")
        axis.grid(alpha=0.18)
        axis.legend(frameon=False)
    fig.suptitle("Period 2K scan gray-axis calibration · no luma grade")
    fig.tight_layout()
    fig.savefig(
        args.output / "v27_scan_neutral_axis.png",
        dpi=180,
        facecolor="#f2efe8",
    )
    plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
