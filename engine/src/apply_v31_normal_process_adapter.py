#!/usr/bin/env python3
"""Apply V31's final normal-process colour boundary to V30 film masters.

Both inputs are already complete, matched 12-bit Rec.709 results from the same
formed 5279 density.  The scan supplies low-frequency dye colour; projection
supplies lightness and high-frequency opponent texture.  No RAW, negative,
grain, DIR, MTF, black, gamma or artistic control is recomputed.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from render_v23_dual_masters import sha256
import v31_profile


def rec709_decode(signal: np.ndarray) -> np.ndarray:
    signal = np.clip(signal, 0.0, 1.0)
    return np.where(
        signal < 0.081,
        signal / 4.5,
        np.power((signal + 0.099) / 1.099, 1.0 / 0.45),
    ).astype(np.float32)


def preserve_luma_and_compress_gamut(
    rgb: np.ndarray,
    target_luma: np.ndarray,
) -> np.ndarray:
    """Fit RGB to [0,1] around exact Rec.709 luma without clipping hue."""
    weights = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    current_luma = np.einsum("...c,c->...", rgb, weights)
    balanced = rgb + (target_luma - current_luma)[..., None]
    delta = balanced - target_luma[..., None]
    positive_limit = np.where(
        delta > 1e-8,
        (1.0 - target_luma[..., None]) / np.maximum(delta, 1e-8),
        np.inf,
    )
    negative_limit = np.where(
        delta < -1e-8,
        target_luma[..., None] / np.maximum(-delta, 1e-8),
        np.inf,
    )
    scale = np.minimum(
        1.0,
        np.min(np.minimum(positive_limit, negative_limit), axis=-1),
    )
    return np.clip(
        target_luma[..., None] + delta * scale[..., None], 0.0, 1.0
    ).astype(np.float32)


def adapt_frame_linear(
    projection: np.ndarray,
    scan: np.ndarray,
    opponent_high_frequency_retention: float = 1.0,
) -> np.ndarray:
    """Apply the V31 colour boundary to matched linear Rec.709 observers.

    Keeping this operation before delivery encoding avoids an otherwise
    redundant ProRes encode/decode generation.  The released V31 file adapter
    below remains a compatibility wrapper around the same linear operation.
    """
    projection = np.asarray(projection, dtype=np.float32)
    scan = np.asarray(scan, dtype=np.float32)
    projection_lab = e.linear_rec709_to_oklab(projection)
    scan_lab = e.linear_rec709_to_oklab(scan)
    sigma = max(
        float(v31_profile.PROFILE["projection_chroma_crossover_sigma_at_2k"])
        * projection.shape[1]
        / 2048.0,
        0.05,
    )
    projection_low_ab = cv2.GaussianBlur(
        projection_lab[..., 1:3], (0, 0), sigma,
        borderType=cv2.BORDER_REFLECT,
    )
    scan_low_ab = cv2.GaussianBlur(
        scan_lab[..., 1:3], (0, 0), sigma,
        borderType=cv2.BORDER_REFLECT,
    )
    target_lab = projection_lab.copy()
    target_lab[..., 1:3] = (
        scan_low_ab
        + float(opponent_high_frequency_retention)
        * (projection_lab[..., 1:3] - projection_low_ab)
    )
    target_rgb = e.oklab_to_linear_rec709(target_lab)
    projection_luma = np.einsum(
        "...c,c->...", projection, [0.2126, 0.7152, 0.0722]
    ).astype(np.float32)
    return preserve_luma_and_compress_gamut(target_rgb, projection_luma)


def adapt_frame(
    projection_signal: np.ndarray,
    scan_signal: np.ndarray,
) -> np.ndarray:
    projection = rec709_decode(projection_signal)
    scan = rec709_decode(scan_signal)
    corrected = adapt_frame_linear(projection, scan)
    return e.bt709_encode(corrected).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("projection", type=Path)
    parser.add_argument("scan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--opencv-threads", type=int, default=8)
    args = parser.parse_args()
    cv2.setNumThreads(args.opencv_threads)
    width, height, fps = e.probe_video(args.projection)
    scan_width, scan_height, scan_fps = e.probe_video(args.scan)
    if (width, height, fps) != (scan_width, scan_height, scan_fps):
        raise ValueError("projection and scan masters are not matched")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    decode = [
        "ffmpeg", "-v", "error", "-i", "INPUT", "-an",
        "-frames:v", str(args.frames),
        "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
    ]
    projection_decoder = subprocess.Popen(
        [args.projection.as_posix() if value == "INPUT" else value for value in decode],
        stdout=subprocess.PIPE,
    )
    scan_decoder = subprocess.Popen(
        [args.scan.as_posix() if value == "INPUT" else value for value in decode],
        stdout=subprocess.PIPE,
    )
    encoder = subprocess.Popen(
        e.prores_encoder_command(args.output, width, height, fps),
        stdin=subprocess.PIPE,
    )
    assert projection_decoder.stdout and scan_decoder.stdout and encoder.stdin
    frame_bytes = width * height * 3 * 2
    durations: list[float] = []
    total_start = time.perf_counter()
    for frame in range(args.frames):
        mark = time.perf_counter()
        projection_payload = projection_decoder.stdout.read(frame_bytes)
        scan_payload = scan_decoder.stdout.read(frame_bytes)
        if len(projection_payload) != frame_bytes or len(scan_payload) != frame_bytes:
            raise RuntimeError(f"decoded {frame} frames; expected {args.frames}")
        projection = (
            np.frombuffer(projection_payload, dtype="<u2")
            .reshape(height, width, 3)
            .astype(np.float32) / 65535.0
        )
        scan = (
            np.frombuffer(scan_payload, dtype="<u2")
            .reshape(height, width, 3)
            .astype(np.float32) / 65535.0
        )
        corrected = adapt_frame(projection, scan)
        encoder.stdin.write(
            np.rint(np.clip(corrected, 0.0, 1.0) * 65535.0)
            .astype("<u2").tobytes()
        )
        durations.append(time.perf_counter() - mark)
        print(
            f"V31 final adapter frame {frame + 1}/{args.frames} · "
            f"{durations[-1]:.2f}s",
            flush=True,
        )

    projection_decoder.stdout.close()
    scan_decoder.stdout.close()
    encoder.stdin.close()
    if projection_decoder.wait() or scan_decoder.wait() or encoder.wait():
        raise RuntimeError("V31 adapter pipeline failed")
    e.finalize_prores_rec709_metadata(args.output)
    timing = {
        "clock": "time.perf_counter monotonic wall clock",
        "machine": {
            "system": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "opencv_threads": args.opencv_threads,
        },
        "frames": args.frames,
        "total_wall_seconds": time.perf_counter() - total_start,
        "mean_seconds_per_frame": float(np.mean(durations)),
        "median_seconds_per_frame": float(np.median(durations)),
    }
    manifest = {
        "release": v31_profile.PROFILE["name"],
        "profile": "v31",
        "source_projection": str(args.projection),
        "source_projection_sha256": sha256(args.projection),
        "source_scan": str(args.scan),
        "source_scan_sha256": sha256(args.scan),
        "master_sha256": sha256(args.output),
        "dimensions": [width, height], "fps": fps, "frames": args.frames,
        "output": "12-bit ProRes 4444 · Rec.709 1-1-1",
        "normal_process_boundary": v31_profile.PROFILE["process_constraint"],
        "colour_operation": (
            "scan low-frequency OKLab a/b plus projection high-frequency "
            "opponent residual; exact per-pixel projection Rec.709 linear luma"
        ),
        "crossover_sigma_at_2k": v31_profile.PROFILE[
            "projection_chroma_crossover_sigma_at_2k"
        ],
        "creative_grade": "none",
        "timing": timing,
    }
    (args.output.parent / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(timing, indent=2), flush=True)


if __name__ == "__main__":
    main()
