#!/usr/bin/env python3
"""Sample a finished feature and measure its display-referred grading envelope.

This is deliberately a finishing-reference tool, not a film-stock measurement
tool.  It decodes a sparse set of downscaled frames, rejects near-black
transitions, records tone/chroma statistics, and creates a representative
contact sheet without modifying the source movie.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


BT709_LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    return np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        np.power((rgb + 0.055) / 1.055, 2.4),
    )


def linear_srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    lms = np.einsum(
        "...c,dc->...d",
        rgb,
        np.array(
            [
                [0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005],
            ],
            dtype=np.float32,
        ),
    )
    lms_root = np.cbrt(np.maximum(lms, 0.0))
    return np.einsum(
        "...c,dc->...d",
        lms_root,
        np.array(
            [
                [0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660],
            ],
            dtype=np.float32,
        ),
    )


def frame_metrics(frame_u8: np.ndarray, timestamp: float) -> dict:
    rgb = frame_u8.astype(np.float32) / 255.0
    y_prime = np.einsum("...c,c->...", rgb, BT709_LUMA)
    linear = srgb_to_linear(rgb)
    lab = linear_srgb_to_oklab(linear)
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    mid_mask = (lab[..., 0] >= 0.12) & (lab[..., 0] <= 0.90)
    mid_chroma = chroma[mid_mask]
    if mid_chroma.size == 0:
        mid_chroma = chroma.reshape(-1)
    percentiles = np.percentile(
        y_prime, [0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]
    )
    return {
        "timestamp_seconds": float(timestamp),
        "y_p001": float(percentiles[0]),
        "y_p01": float(percentiles[1]),
        "y_p05": float(percentiles[2]),
        "y_p10": float(percentiles[3]),
        "y_p25": float(percentiles[4]),
        "y_p50": float(percentiles[5]),
        "y_p75": float(percentiles[6]),
        "y_p90": float(percentiles[7]),
        "y_p95": float(percentiles[8]),
        "y_p99": float(percentiles[9]),
        "y_p999": float(percentiles[10]),
        "contrast_p95_p05": float(percentiles[8] - percentiles[2]),
        "fraction_at_black_2_codes": float(np.mean(y_prime <= (2.0 / 255.0))),
        "fraction_at_white_2_codes": float(np.mean(y_prime >= (253.0 / 255.0))),
        "oklab_chroma_median": float(np.median(mid_chroma)),
        "oklab_chroma_p90": float(np.percentile(mid_chroma, 90)),
        "oklab_mean_a": float(np.mean(lab[..., 1])),
        "oklab_mean_b": float(np.mean(lab[..., 2])),
    }


def timestamp_label(seconds: float) -> str:
    seconds_int = int(round(seconds))
    hours, remainder = divmod(seconds_int, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def select_examples(metrics: list[dict], usable_indices: list[int]) -> list[tuple[str, int]]:
    def rank(name: str, fraction: float) -> int:
        ordered = sorted(usable_indices, key=lambda index: metrics[index][name])
        position = int(round(fraction * (len(ordered) - 1)))
        return ordered[position]

    candidates = [
        ("deep black", rank("y_p01", 0.05)),
        ("raised black", rank("y_p01", 0.90)),
        ("dark scene", rank("y_p50", 0.15)),
        ("typical scene", rank("y_p50", 0.50)),
        ("bright scene", rank("y_p50", 0.85)),
        ("soft contrast", rank("contrast_p95_p05", 0.15)),
        ("hard contrast", rank("contrast_p95_p05", 0.90)),
        ("muted colour", rank("oklab_chroma_p90", 0.15)),
        ("rich colour", rank("oklab_chroma_p90", 0.90)),
        ("warm bias", rank("oklab_mean_b", 0.95)),
        ("cool bias", rank("oklab_mean_b", 0.05)),
        ("bright highlights", rank("y_p999", 0.95)),
    ]
    selected: list[tuple[str, int]] = []
    used: set[int] = set()
    for label, index in candidates:
        if index in used:
            alternatives = sorted(
                usable_indices,
                key=lambda other: abs(other - index),
            )
            index = next((other for other in alternatives if other not in used), index)
        used.add(index)
        selected.append((label, index))
    return selected


def build_contact_sheet(
    frames: np.ndarray,
    metrics: list[dict],
    selected: list[tuple[str, int]],
    output_path: Path,
) -> None:
    tile_width, tile_height = frames.shape[2], frames.shape[1]
    label_height = 40
    columns = 3
    rows = (len(selected) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * (tile_height + label_height)), "#151515")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=15)
    for item, (label, index) in enumerate(selected):
        x = (item % columns) * tile_width
        y = (item // columns) * (tile_height + label_height)
        sheet.paste(Image.fromarray(frames[index]), (x, y))
        entry = metrics[index]
        line = (
            f"{label}  {timestamp_label(entry['timestamp_seconds'])}   "
            f"P1 {entry['y_p01']:.3f}  P50 {entry['y_p50']:.3f}  "
            f"P99 {entry['y_p99']:.3f}  C90 {entry['oklab_chroma_p90']:.3f}"
        )
        draw.text((x + 8, y + tile_height + 9), line, font=font, fill="#eeeeee")
    sheet.save(output_path, quality=95)


def distribution(metrics: list[dict], indices: list[int], key: str) -> dict:
    values = np.array([metrics[index][key] for index in indices], dtype=np.float64)
    return {
        "p10": float(np.percentile(values, 10)),
        "median": float(np.median(values)),
        "p90": float(np.percentile(values, 90)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--start", type=float, default=120.0)
    parser.add_argument("--end-padding", type=float, default=180.0)
    parser.add_argument("--width", type=int, default=480)
    args = parser.parse_args()

    metadata = probe(args.input)
    video = next(stream for stream in metadata["streams"] if stream["codec_type"] == "video")
    duration = float(metadata["format"]["duration"])
    sample_duration = max(duration - args.start - args.end_padding, args.interval)
    height = int(round(args.width * int(video["height"]) / int(video["width"])))
    if height % 2:
        height += 1

    command = [
        "ffmpeg",
        "-v",
        "error",
        "-ss",
        str(args.start),
        "-i",
        str(args.input),
        "-t",
        str(sample_duration),
        "-an",
        "-sn",
        "-vf",
        f"fps=1/{args.interval},scale={args.width}:{height}:flags=lanczos",
        "-pix_fmt",
        "rgb24",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    result = subprocess.run(command, check=True, capture_output=True)
    frame_bytes = args.width * height * 3
    frame_count = len(result.stdout) // frame_bytes
    frames = np.frombuffer(result.stdout[: frame_count * frame_bytes], dtype=np.uint8).reshape(
        frame_count, height, args.width, 3
    )
    metrics = [
        frame_metrics(frame, args.start + index * args.interval)
        for index, frame in enumerate(frames)
    ]
    usable_indices = [
        index
        for index, entry in enumerate(metrics)
        if entry["y_p50"] > 0.015
        and entry["y_p99"] > 0.08
        and entry["fraction_at_black_2_codes"] < 0.80
    ]
    if len(usable_indices) < 12:
        raise RuntimeError("Too few usable frames after transition rejection")

    keys = [
        "y_p001",
        "y_p01",
        "y_p05",
        "y_p50",
        "y_p95",
        "y_p99",
        "y_p999",
        "contrast_p95_p05",
        "fraction_at_black_2_codes",
        "fraction_at_white_2_codes",
        "oklab_chroma_median",
        "oklab_chroma_p90",
    ]
    selected = select_examples(metrics, usable_indices)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    build_contact_sheet(
        frames,
        metrics,
        selected,
        args.output_dir / "charlies_angels_reference_contact_sheet.jpg",
    )

    report = {
        "source": str(args.input),
        "role": "finished Blu-ray grading reference; not a direct 5279 stock measurement",
        "limitations": [
            "8-bit H.264, 4:2:0 chroma sampling",
            "Blu-ray mastering and scene-by-scene creative grading are baked in",
            "sparse downscaled frames are suitable for tone and colour envelopes, not grain-size calibration",
            "container does not explicitly signal colour primaries, transfer, matrix, or range; HD Rec.709 limited-range decoding is assumed",
        ],
        "source_video": {
            "codec": video.get("codec_name"),
            "profile": video.get("profile"),
            "width": int(video["width"]),
            "height": int(video["height"]),
            "pixel_format": video.get("pix_fmt"),
            "frame_rate": video.get("avg_frame_rate"),
            "bits_per_raw_sample": video.get("bits_per_raw_sample"),
            "duration_seconds": duration,
            "container_bit_rate": int(metadata["format"].get("bit_rate", 0)),
            "colour_primaries": video.get("color_primaries", "unspecified"),
            "colour_transfer": video.get("color_transfer", "unspecified"),
            "colour_matrix": video.get("color_space", "unspecified"),
            "colour_range": video.get("color_range", "unspecified"),
        },
        "sampling": {
            "start_seconds": args.start,
            "end_padding_seconds": args.end_padding,
            "interval_seconds": args.interval,
            "decoded_frame_count": frame_count,
            "usable_frame_count": len(usable_indices),
            "analysis_resolution": [args.width, height],
        },
        "across_usable_frames": {
            key: distribution(metrics, usable_indices, key) for key in keys
        },
        "selected_examples": [
            {"label": label, **metrics[index]} for label, index in selected
        ],
        "all_frame_metrics": metrics,
    }
    (args.output_dir / "charlies_angels_reference_metrics.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
