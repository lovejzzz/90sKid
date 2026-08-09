#!/usr/bin/env python3
"""Validate V29 full-motion masters and record scene-wide delivery metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


def probe(path: Path) -> dict[str, object]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def video_stream(info: dict[str, object]) -> dict[str, object]:
    return next(stream for stream in info["streams"] if stream["codec_type"] == "video")


def stream_or_none(info: dict[str, object], kind: str) -> dict[str, object] | None:
    return next((stream for stream in info["streams"] if stream["codec_type"] == kind), None)


def decoded_frame(path: Path, frame: int, width: int, height: int) -> np.ndarray:
    payload = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1",
            "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)


def frame_metrics(frame: np.ndarray) -> dict[str, object]:
    unit = frame.astype(np.float32) / 65535.0
    luma = np.einsum("...c,c->...", unit, [0.2126, 0.7152, 0.0722])
    return {
        "rgb48_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
        "luma_percentiles": {
            key: float(value)
            for key, value in zip(
                ("p0_1", "p1", "p50", "p99", "p99_9"),
                np.percentile(luma, [0.1, 1.0, 50.0, 99.0, 99.9]),
                strict=True,
            )
        },
        "white_clip_fraction": float(np.mean(np.all(frame >= 65520, axis=-1))),
        "black_clip_fraction": float(np.mean(np.all(frame <= 16, axis=-1))),
        "channel_mean": [float(value) for value in np.mean(unit, axis=(0, 1))],
    }


def full_motion_metrics(path: Path, width: int, height: int, frames: int) -> dict[str, object]:
    # A native-resolution centre crop keeps the grain sampling scale intact
    # while bounding validation memory and decode time.
    crop_width, crop_height = 1024, 768
    x = (width - crop_width) // 2
    y = (height - crop_height) // 2
    process = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", f"crop={crop_width}:{crop_height}:{x}:{y}",
            "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    assert process.stdout is not None
    frame_bytes = crop_width * crop_height * 3 * 2
    luma_percentiles: list[np.ndarray] = []
    white_clip: list[float] = []
    black_clip: list[float] = []
    high_frequency_rms: list[float] = []
    high_frequency_correlations: list[float] = []
    previous_high: np.ndarray | None = None
    decoded = 0
    while decoded < frames:
        payload = process.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            break
        image = np.frombuffer(payload, dtype="<u2").reshape(crop_height, crop_width, 3)
        unit = image.astype(np.float32) / 65535.0
        luma = np.einsum("...c,c->...", unit, [0.2126, 0.7152, 0.0722]).astype(np.float32)
        luma_percentiles.append(np.percentile(luma, [0.1, 1.0, 50.0, 99.0, 99.9]))
        white_clip.append(float(np.mean(np.all(image >= 65520, axis=-1))))
        black_clip.append(float(np.mean(np.all(image <= 16, axis=-1))))
        low = cv2.GaussianBlur(luma, (0, 0), 1.2, borderType=cv2.BORDER_REFLECT)
        high = luma - low
        high_frequency_rms.append(float(np.sqrt(np.mean(np.square(high)))))
        if previous_high is not None:
            a = previous_high.ravel().astype(np.float64)
            b = high.ravel().astype(np.float64)
            a -= a.mean()
            b -= b.mean()
            denominator = np.sqrt(np.dot(a, a) * np.dot(b, b))
            high_frequency_correlations.append(
                float(np.dot(a, b) / denominator) if denominator > 0.0 else 0.0
            )
        previous_high = high
        decoded += 1
    process.stdout.close()
    if process.wait() != 0 or decoded != frames:
        raise RuntimeError(f"decoded {decoded} validation frames; expected {frames}")
    percentile_array = np.asarray(luma_percentiles)
    return {
        "crop": [x, y, crop_width, crop_height],
        "frames": decoded,
        "per_frame_luma_percentile_ranges": {
            name: [float(np.min(percentile_array[:, index])), float(np.max(percentile_array[:, index]))]
            for index, name in enumerate(("p0_1", "p1", "p50", "p99", "p99_9"))
        },
        "maximum_white_clip_fraction": float(np.max(white_clip)),
        "maximum_black_clip_fraction": float(np.max(black_clip)),
        "high_frequency_rms_range": [
            float(np.min(high_frequency_rms)), float(np.max(high_frequency_rms))
        ],
        "successive_high_frequency_correlation": {
            "median": float(np.median(high_frequency_correlations)),
            "p05": float(np.percentile(high_frequency_correlations, 5.0)),
            "p95": float(np.percentile(high_frequency_correlations, 95.0)),
            "interpretation": (
                "real-scene motion plus new per-frame emulsion; not a stock-specific NPS measurement"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("release", type=Path)
    parser.add_argument("--probe-frame", type=int, default=82)
    parser.add_argument("--probe-release", type=Path)
    args = parser.parse_args()

    source_info = probe(args.source)
    source_video = video_stream(source_info)
    expected_frames = int(source_video["nb_frames"])
    expected_width = int(source_video["width"])
    expected_height = int(source_video["height"])
    source_audio = stream_or_none(source_info, "audio")
    source_data = stream_or_none(source_info, "data")
    source_timecode = (
        source_info.get("format", {}).get("tags", {}).get("timecode")
        or (source_data or {}).get("tags", {}).get("timecode")
    )
    results: dict[str, object] = {"source": str(args.source), "observers": {}}
    failures: list[str] = []

    for observer, directory in (("projection", "projection"), ("scan", "bluray_scan")):
        master = args.release / directory / "05_emulsion_master_prores4444.mov"
        info = probe(master)
        video = video_stream(info)
        audio = stream_or_none(info, "audio")
        data = stream_or_none(info, "data")
        checks = {
            "dimensions": [int(video["width"]), int(video["height"])] == [expected_width, expected_height],
            "frame_count": int(video["nb_frames"]) == expected_frames,
            "frame_rate": video["avg_frame_rate"] == source_video["avg_frame_rate"],
            "codec": video["codec_name"] == "prores",
            "pixel_format": video["pix_fmt"] == "yuv444p12le",
            "bit_depth": int(video["bits_per_raw_sample"]) == 12,
            "rec709_111": (
                video.get("color_primaries") == "bt709"
                and video.get("color_transfer") == "bt709"
                and video.get("color_space") == "bt709"
            ),
            "audio_codec": audio is not None and audio.get("codec_name") == "pcm_s24le",
            "audio_layout": (
                audio is not None
                and int(audio.get("sample_rate", 0)) == int(source_audio.get("sample_rate", 0))
                and int(audio.get("channels", 0)) == int(source_audio.get("channels", 0))
                and int(audio.get("bits_per_raw_sample", 0)) == 24
            ),
            "timecode": (
                video.get("tags", {}).get("timecode") == source_timecode
                and (data or {}).get("tags", {}).get("timecode") == source_timecode
                and data is not None
            ),
        }
        failures.extend(f"{observer}:{name}" for name, passed in checks.items() if not passed)
        selected = {}
        for frame_number in (0, args.probe_frame, args.probe_frame + 1, expected_frames - 1):
            selected[str(frame_number)] = frame_metrics(
                decoded_frame(master, frame_number, expected_width, expected_height)
            )
        parity = None
        if args.probe_release is not None:
            probe_master = args.probe_release / directory / "05_emulsion_master_prores4444.mov"
            reference = decoded_frame(probe_master, 0, expected_width, expected_height)
            full = decoded_frame(master, args.probe_frame, expected_width, expected_height)
            parity = {
                "full_frame": args.probe_frame,
                "standalone_frame": 0,
                "array_equal": bool(np.array_equal(reference, full)),
                "standalone_rgb48_sha256": hashlib.sha256(reference.tobytes()).hexdigest(),
                "full_rgb48_sha256": hashlib.sha256(full.tobytes()).hexdigest(),
            }
            if not parity["array_equal"]:
                failures.append(f"{observer}:absolute_frame_segment_parity")
        results["observers"][observer] = {
            "master": str(master),
            "checks": checks,
            "selected_frame_metrics": selected,
            "absolute_frame_segment_parity": parity,
            "full_motion_metrics": full_motion_metrics(
                master, expected_width, expected_height, expected_frames
            ),
        }

    results["passed"] = not failures
    results["failures"] = failures
    destination = args.release / "validation.json"
    destination.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": not failures, "failures": failures, "report": str(destination)}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
