#!/usr/bin/env python3
"""Validate the three native-resolution V30 one-second comparison renders."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


CLIPS = ("T002", "T020", "T032")
OBSERVERS = {"projection": "projection", "scan": "bluray_scan"}
MASTER_NAME = "05_emulsion_master_prores4444.mov"


def run_json(command: list[str]) -> dict[str, object]:
    result = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def probe(path: Path) -> dict[str, object]:
    return run_json(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    )


def video_stream(info: dict[str, object]) -> dict[str, object]:
    return next(stream for stream in info["streams"] if stream["codec_type"] == "video")


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


def preview_frame(path: Path, frame: int) -> np.ndarray:
    width, height = 960, 720
    payload = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", f"select=eq(n\\,{frame}),scale={width}:{height}:flags=area",
            "-frames:v", "1", "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)


def srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(np.float64) / 65535.0
    linear = np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        np.power((rgb + 0.055) / 1.055, 2.4),
    )
    l = np.cbrt(
        0.4122214708 * linear[..., 0]
        + 0.5363325363 * linear[..., 1]
        + 0.0514459929 * linear[..., 2]
    )
    m = np.cbrt(
        0.2119034982 * linear[..., 0]
        + 0.6806995451 * linear[..., 1]
        + 0.1073969566 * linear[..., 2]
    )
    s = np.cbrt(
        0.0883024619 * linear[..., 0]
        + 0.2817188376 * linear[..., 1]
        + 0.6299787005 * linear[..., 2]
    )
    return np.stack(
        [
            0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
        ],
        axis=-1,
    )


def frame_metrics(frame: np.ndarray) -> dict[str, object]:
    unit = frame.astype(np.float32) / 65535.0
    luma = np.einsum("...c,c->...", unit, [0.2126, 0.7152, 0.0722])
    return {
        "rgb48_sha256": hashlib.sha256(frame.tobytes()).hexdigest(),
        "luma_percentiles": {
            label: float(value)
            for label, value in zip(
                ("p0_1", "p1", "p50", "p99", "p99_9"),
                np.percentile(luma, [0.1, 1.0, 50.0, 99.0, 99.9]),
                strict=True,
            )
        },
        "white_clip_fraction": float(np.mean(np.all(frame >= 65520, axis=-1))),
        "black_clip_fraction": float(np.mean(np.all(frame <= 16, axis=-1))),
        "channel_mean": [float(value) for value in np.mean(unit, axis=(0, 1))],
    }


def motion_metrics(path: Path, width: int, height: int, frames: int) -> dict[str, object]:
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
    rms: list[float] = []
    correlations: list[float] = []
    previous: np.ndarray | None = None
    decoded = 0
    while decoded < frames:
        payload = process.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            break
        image = np.frombuffer(payload, dtype="<u2").reshape(crop_height, crop_width, 3)
        unit = image.astype(np.float32) / 65535.0
        luma = np.einsum("...c,c->...", unit, [0.2126, 0.7152, 0.0722]).astype(np.float32)
        high = luma - cv2.GaussianBlur(luma, (0, 0), 1.2, borderType=cv2.BORDER_REFLECT)
        rms.append(float(np.sqrt(np.mean(np.square(high)))))
        if previous is not None:
            a = previous.ravel().astype(np.float64)
            b = high.ravel().astype(np.float64)
            a -= a.mean()
            b -= b.mean()
            denominator = np.sqrt(np.dot(a, a) * np.dot(b, b))
            correlations.append(float(np.dot(a, b) / denominator) if denominator else 0.0)
        previous = high
        decoded += 1
    process.stdout.close()
    if process.wait() != 0 or decoded != frames:
        raise RuntimeError(f"decoded {decoded} frames from {path}; expected {frames}")
    return {
        "native_scale_crop": [x, y, crop_width, crop_height],
        "frames": decoded,
        "high_frequency_rms_range": [float(np.min(rms)), float(np.max(rms))],
        "successive_high_frequency_correlation": {
            "median": float(np.median(correlations)),
            "p05": float(np.percentile(correlations, 5.0)),
            "p95": float(np.percentile(correlations, 95.0)),
        },
    }


def observer_colour_difference(projection: np.ndarray, scan: np.ndarray) -> dict[str, object]:
    projected_lab = srgb_to_oklab(projection)
    scan_lab = srgb_to_oklab(scan)
    projected_chroma = np.linalg.norm(projected_lab[..., 1:3], axis=-1)
    scan_chroma = np.linalg.norm(scan_lab[..., 1:3], axis=-1)
    useful = (scan_lab[..., 0] > 0.12) & (scan_lab[..., 0] < 0.88)
    coloured = useful & (scan_chroma > 0.015)
    neutral = useful & (scan_chroma < 0.008)
    hue_projected = np.arctan2(projected_lab[..., 2], projected_lab[..., 1])
    hue_scan = np.arctan2(scan_lab[..., 2], scan_lab[..., 1])
    hue_delta = np.angle(np.exp(1j * (hue_projected - hue_scan)))
    neutral_ab = np.mean(projected_lab[..., 1:3][neutral], axis=0)
    return {
        "coloured_pixel_count": int(np.sum(coloured)),
        "neutral_pixel_count": int(np.sum(neutral)),
        "coloured_median_hue_delta_degrees": float(np.degrees(np.median(hue_delta[coloured]))),
        "coloured_p95_absolute_hue_delta_degrees": float(
            np.degrees(np.percentile(np.abs(hue_delta[coloured]), 95.0))
        ),
        "projection_neutral_mean_oklab_ab": [float(value) for value in neutral_ab],
        "projection_neutral_mean_chroma": float(np.linalg.norm(neutral_ab)),
        "scan_neutral_mean_oklab_ab": [
            float(value) for value in np.mean(scan_lab[..., 1:3][neutral], axis=0)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("--frames", type=int, default=24)
    args = parser.parse_args()

    failures: list[str] = []
    report: dict[str, object] = {"release": str(args.release), "clips": {}}
    for clip in CLIPS:
        source = args.source_directory / f"NJARAW_S001_S001_{clip}.MOV"
        source_video = video_stream(probe(source))
        width, height = int(source_video["width"]), int(source_video["height"])
        fps = source_video["avg_frame_rate"]
        clip_report: dict[str, object] = {"source": str(source), "observers": {}}
        preview: dict[str, np.ndarray] = {}
        for observer, directory in OBSERVERS.items():
            master = args.release / clip / directory / MASTER_NAME
            info = probe(master)
            video = video_stream(info)
            checks = {
                "dimensions": [int(video["width"]), int(video["height"])] == [width, height],
                "frame_count": int(video["nb_frames"]) == args.frames,
                "frame_rate": video["avg_frame_rate"] == fps,
                "codec": video["codec_name"] == "prores" and video.get("profile") == "4444",
                "pixel_format": video["pix_fmt"] == "yuv444p12le",
                "bit_depth": int(video["bits_per_raw_sample"]) == 12,
                "rec709_111": (
                    video.get("color_primaries") == "bt709"
                    and video.get("color_transfer") == "bt709"
                    and video.get("color_space") == "bt709"
                ),
            }
            failures.extend(
                f"{clip}:{observer}:{name}" for name, passed in checks.items() if not passed
            )
            selected = {
                str(frame): frame_metrics(decoded_frame(master, frame, width, height))
                for frame in (0, args.frames // 2, args.frames - 1)
            }
            preview[observer] = preview_frame(master, args.frames // 2)
            clip_report["observers"][observer] = {
                "master": str(master),
                "checks": checks,
                "selected_frame_metrics": selected,
                "motion_metrics": motion_metrics(master, width, height, args.frames),
            }
        colour = observer_colour_difference(preview["projection"], preview["scan"])
        colour_checks = {
            "projection_neutral_is_not_blue_magenta_veil": (
                colour["neutral_pixel_count"] >= 100
                and colour["projection_neutral_mean_chroma"] < 0.012
            ),
            "median_observer_hue_separation_is_bounded": (
                colour["coloured_pixel_count"] >= 100
                and abs(colour["coloured_median_hue_delta_degrees"]) < 15.0
            ),
        }
        failures.extend(
            f"{clip}:colour:{name}" for name, passed in colour_checks.items() if not passed
        )
        clip_report["observer_colour_difference"] = colour
        clip_report["colour_checks"] = colour_checks
        timing_path = args.release / clip / "timing.json"
        clip_report["timing"] = json.loads(timing_path.read_text(encoding="utf-8"))
        report["clips"][clip] = clip_report

    report["passed"] = not failures
    report["failures"] = failures
    destination = args.release / "validation.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": not failures, "failures": failures, "report": str(destination)}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
