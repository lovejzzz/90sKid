"""Inventory V21 high-exposure use and 10-bit Cineon headroom.

Every ProRes RAW frame is decoded by AVFoundation as extended-linear BT.2020
float32.  The inventory uses an area-reduced 720 x 540 raster for tractable
all-frame statistics, then records the frames with the largest log-exposure and
Cineon pre-clip code for later full controlled A/B testing.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT = ROOT / "experiments" / "emulsion_reconstruction"
sys.path.insert(0, str(EXPERIMENT / "src"))
import emulsion_experiment as emulsion


INPUT = Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV")
DECODER = Path("/tmp/prores_raw_float_decode")
OUTPUT = Path(__file__).resolve().parent
SOURCE_WIDTH = 5760
SOURCE_HEIGHT = 4320
FRAME_COUNT = 165
TEST_WIDTH = 720
TEST_HEIGHT = 540
EXPOSURE_STOPS = 0.45
FRAME_BYTES = SOURCE_WIDTH * SOURCE_HEIGHT * 3 * 4
THRESHOLDS = (0.0, 0.5, 1.0)


def exact_read(stream, byte_count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = byte_count
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def frame_metrics(raw: np.ndarray, frame_index: int) -> dict[str, object]:
    reduced = cv2.resize(raw, (TEST_WIDTH, TEST_HEIGHT), interpolation=cv2.INTER_AREA)
    film_rgb = emulsion.scene_to_5279_film_rgb(
        reduced,
        exposure_stops=EXPOSURE_STOPS,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    records = emulsion.film_records_from_rgb(film_rgb)
    loge = np.log10(np.maximum(records, 1e-8)) - 1.0
    density = emulsion.develop_5279_record_density_from_log_exposure(loge)
    scanner_density = emulsion.scanner_density_from_total_record_density(density)
    gain = 0.700 / np.maximum(emulsion.NEUTRAL_MID_SCANNER_DENSITY, 1e-6)
    cineon_code_unclipped = 95.0 + scanner_density * gain / 0.002

    result: dict[str, object] = {
        "frame": frame_index,
        "raw_extended_linear_max_rgb": np.max(raw, axis=(0, 1)).astype(float).tolist(),
        "loge_max_rgb": np.max(loge, axis=(0, 1)).astype(float).tolist(),
        "cineon_code_unclipped_max_rgb": np.max(
            cineon_code_unclipped, axis=(0, 1)
        ).astype(float).tolist(),
        "cineon_1023_clip_percent_rgb": (
            100.0 * np.mean(cineon_code_unclipped > 1023.0, axis=(0, 1))
        ).astype(float).tolist(),
    }
    for threshold in THRESHOLDS:
        label = str(threshold).replace(".", "p")
        result[f"loge_gt_{label}_percent_rgb"] = (
            100.0 * np.mean(loge > threshold, axis=(0, 1))
        ).astype(float).tolist()
    return result


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    decoder = subprocess.Popen(
        [str(DECODER), str(INPUT), "0", str(FRAME_COUNT)],
        stdout=subprocess.PIPE,
    )
    assert decoder.stdout is not None
    frames: list[dict[str, object]] = []
    for frame_index in range(FRAME_COUNT):
        payload = exact_read(decoder.stdout, FRAME_BYTES)
        if len(payload) != FRAME_BYTES:
            raise RuntimeError(
                f"frame {frame_index}: decoder returned {len(payload)} bytes, "
                f"expected {FRAME_BYTES}"
            )
        raw = np.frombuffer(payload, dtype="<f4").reshape(
            SOURCE_HEIGHT, SOURCE_WIDTH, 3
        )
        metrics = frame_metrics(raw, frame_index)
        frames.append(metrics)
        print(
            frame_index,
            metrics["loge_max_rgb"],
            metrics["cineon_code_unclipped_max_rgb"],
            flush=True,
        )
    decoder.stdout.close()
    return_code = decoder.wait()
    if return_code != 0:
        raise RuntimeError(f"decoder exited with {return_code}")

    channel_names = ("R", "G", "B")
    summary: dict[str, object] = {
        "input": str(INPUT),
        "input_codec": "12-bit ProRes RAW HQ",
        "decode": "AVFoundation extended-linear BT.2020 RGB float32",
        "frames_inventory": FRAME_COUNT,
        "source_dimensions": [SOURCE_WIDTH, SOURCE_HEIGHT],
        "inventory_dimensions": [TEST_WIDTH, TEST_HEIGHT],
        "inventory_sampling": "all frames, area-reduced in extended-linear light",
        "exposure_stops": EXPOSURE_STOPS,
        "raw_colour_transform": "Panasonic official GH7-compatible camera LUT",
        "sensor_noise_treatment": "photochemical edge-aware separation before virtual exposure",
        "stock_curve_published_domain_loge": [-4.0, 0.0],
        "v21_curve_extension_loge": [0.5, 1.0],
        "cineon_reference": "10-bit; D-min code 95; 0.002 density/CV",
        "channels": {},
    }
    channels = summary["channels"]
    assert isinstance(channels, dict)
    for channel, name in enumerate(channel_names):
        max_loge_frame = max(frames, key=lambda row: row["loge_max_rgb"][channel])
        max_code_frame = max(
            frames, key=lambda row: row["cineon_code_unclipped_max_rgb"][channel]
        )
        channels[name] = {
            "max_loge": max_loge_frame["loge_max_rgb"][channel],
            "max_loge_frame": max_loge_frame["frame"],
            "max_cineon_code_unclipped": max_code_frame[
                "cineon_code_unclipped_max_rgb"
            ][channel],
            "max_cineon_code_frame": max_code_frame["frame"],
            "frames_with_any_loge_gt_0": sum(
                row["loge_gt_0p0_percent_rgb"][channel] > 0 for row in frames
            ),
            "frames_with_any_loge_gt_0p5": sum(
                row["loge_gt_0p5_percent_rgb"][channel] > 0 for row in frames
            ),
            "frames_with_any_loge_gt_1": sum(
                row["loge_gt_1p0_percent_rgb"][channel] > 0 for row in frames
            ),
            "frames_with_any_cineon_1023_clip": sum(
                row["cineon_1023_clip_percent_rgb"][channel] > 0 for row in frames
            ),
            "maximum_frame_pixel_percent_loge_gt_0": max(
                row["loge_gt_0p0_percent_rgb"][channel] for row in frames
            ),
            "maximum_frame_pixel_percent_loge_gt_0p5": max(
                row["loge_gt_0p5_percent_rgb"][channel] for row in frames
            ),
            "maximum_frame_pixel_percent_loge_gt_1": max(
                row["loge_gt_1p0_percent_rgb"][channel] for row in frames
            ),
            "maximum_frame_pixel_percent_cineon_1023_clip": max(
                row["cineon_1023_clip_percent_rgb"][channel] for row in frames
            ),
        }

    with (OUTPUT / "frame_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "frame",
                *[f"loge_max_{name}" for name in channel_names],
                *[f"loge_gt_0_percent_{name}" for name in channel_names],
                *[f"loge_gt_0p5_percent_{name}" for name in channel_names],
                *[f"loge_gt_1_percent_{name}" for name in channel_names],
                *[f"cineon_unclipped_max_{name}" for name in channel_names],
                *[f"cineon_1023_clip_percent_{name}" for name in channel_names],
            ]
        )
        for row in frames:
            writer.writerow(
                [
                    row["frame"],
                    *row["loge_max_rgb"],
                    *row["loge_gt_0p0_percent_rgb"],
                    *row["loge_gt_0p5_percent_rgb"],
                    *row["loge_gt_1p0_percent_rgb"],
                    *row["cineon_code_unclipped_max_rgb"],
                    *row["cineon_1023_clip_percent_rgb"],
                ]
            )
    (OUTPUT / "inventory_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
