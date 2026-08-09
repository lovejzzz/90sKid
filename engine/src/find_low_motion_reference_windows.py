#!/usr/bin/env python3
"""Locate low-motion reference windows without decoding a feature to disk."""

from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=134)
    parser.add_argument("--sample-fps", type=float, default=6.0)
    parser.add_argument("--window-seconds", type=float, default=2.0)
    parser.add_argument("--start", type=float, default=120.0)
    parser.add_argument("--end-padding", type=float, default=180.0)
    parser.add_argument("--count", type=int, default=24)
    return parser.parse_args()


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def main() -> None:
    args = parse_args()
    duration = probe_duration(args.input)
    sample_duration = max(0.0, duration - args.start - args.end_padding)
    window_frames = max(3, round(args.window_seconds * args.sample_fps))
    frame_bytes = args.width * args.height
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
        "-vf",
        f"fps={args.sample_fps},scale={args.width}:{args.height}:flags=area,format=gray",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "gray",
        "pipe:1",
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    assert process.stdout is not None

    frames: deque[np.ndarray] = deque(maxlen=window_frames)
    diffs: deque[float] = deque(maxlen=window_frames - 1)
    candidates: list[dict[str, float]] = []
    previous: np.ndarray | None = None
    index = 0
    while True:
        payload = process.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            break
        frame = np.frombuffer(payload, dtype=np.uint8).reshape(args.height, args.width)
        if previous is not None:
            diffs.append(float(np.mean(cv2.absdiff(previous, frame))) / 255.0)
        frames.append(frame.copy())
        previous = frame
        index += 1
        if len(frames) != window_frames or len(diffs) != window_frames - 1:
            continue
        stack = np.stack(frames).astype(np.float32) / 255.0
        mean_frame = np.mean(stack, axis=0)
        brightness = float(np.mean(mean_frame))
        texture = float(np.std(cv2.Laplacian(mean_frame, cv2.CV_32F)))
        motion = float(np.median(np.asarray(diffs)))
        motion_p90 = float(np.percentile(np.asarray(diffs), 90))
        if 0.06 <= brightness <= 0.90 and texture >= 0.010:
            centre_index = index - 0.5 * window_frames
            candidates.append(
                {
                    "timestamp_seconds": args.start + centre_index / args.sample_fps,
                    "median_frame_difference": motion,
                    "p90_frame_difference": motion_p90,
                    "mean_luma": brightness,
                    "laplacian_texture": texture,
                }
            )

    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"ffmpeg failed with status {return_code}")

    candidates.sort(
        key=lambda item: (
            item["median_frame_difference"] + 0.35 * item["p90_frame_difference"],
            -item["laplacian_texture"],
        )
    )
    selected: list[dict[str, float]] = []
    for candidate in candidates:
        if all(
            abs(candidate["timestamp_seconds"] - prior["timestamp_seconds"]) >= 8.0
            for prior in selected
        ):
            selected.append(candidate)
        if len(selected) == args.count:
            break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "source": str(args.input),
        "role": "candidate finder only; final temporal measurements require native-rate inspection",
        "sample_fps": args.sample_fps,
        "window_seconds": args.window_seconds,
        "analysis_dimensions": [args.width, args.height],
        "selected": selected,
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
