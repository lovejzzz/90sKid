#!/usr/bin/env python3
"""Build a 24-frame SMPTE ST 428-1 DCDM X'Y'Z' TIFF test sequence."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from apply_v31_normal_process_adapter import rec709_decode
from render_v23_dual_masters import sha256


DCDM_WIDTH = 2880
DCDM_HEIGHT = 2160
DCDM_REFERENCE_LUMINANCE = np.float32(48.0)
DCDM_ENCODING_PEAK = np.float32(52.37)


def encode_dcdm_xyz(linear_rec709: np.ndarray) -> np.ndarray:
    xyz = np.einsum(
        "...c,dc->...d", linear_rec709, e.REC709_TO_XYZ_D65
    ).astype(np.float32)
    normalized = np.clip(
        xyz * (DCDM_REFERENCE_LUMINANCE / DCDM_ENCODING_PEAK),
        0.0,
        1.0,
    )
    code12 = np.rint(np.power(normalized, 1.0 / 2.6) * 4095.0).astype(
        np.uint16
    )
    return np.left_shift(code12, 4)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--composition", required=True)
    parser.add_argument("--frames", type=int, default=24)
    args = parser.parse_args()
    reel_name = f"{args.composition}.Reel_1"
    reel = args.output / reel_name
    reel.mkdir(parents=True, exist_ok=True)
    width, height, source_fps = e.probe_video(args.input)
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(args.input), "-an",
            "-frames:v", str(args.frames), "-pix_fmt", "rgb48le",
            "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    assert decoder.stdout is not None
    frame_bytes = width * height * 3 * 2
    durations: list[float] = []
    started = time.perf_counter()
    files: list[dict[str, object]] = []
    for frame in range(args.frames):
        mark = time.perf_counter()
        payload = decoder.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            raise RuntimeError(f"decoded {frame} frames; expected {args.frames}")
        signal = (
            np.frombuffer(payload, dtype="<u2")
            .reshape(height, width, 3)
            .astype(np.float32)
            / 65535.0
        )
        linear = rec709_decode(signal)
        active = cv2.resize(
            linear, (DCDM_WIDTH, DCDM_HEIGHT), interpolation=cv2.INTER_AREA
        )
        xyz16 = encode_dcdm_xyz(active)
        destination = reel / f"{reel_name}.{frame + 1:05d}.tif"
        if not cv2.imwrite(
            str(destination),
            xyz16[..., ::-1],
            [cv2.IMWRITE_TIFF_COMPRESSION, 1],
        ):
            raise RuntimeError(f"could not write {destination}")
        files.append(
            {
                "name": destination.name,
                "sha256": sha256(destination),
                "bytes": destination.stat().st_size,
            }
        )
        durations.append(time.perf_counter() - mark)
        print(
            f"V32 DCDM frame {frame + 1}/{args.frames} · "
            f"{durations[-1]:.2f}s",
            flush=True,
        )
    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError("DCDM source decode failed")
    manifest = {
        "release": "V32 ST 428-1 DCDM test sequence",
        "scope": (
            "appearance-preserving DCDM test sequence from the completed V31 "
            "projection observer; not a packaged or encrypted DCP"
        ),
        "source": str(args.input),
        "source_sha256": sha256(args.input),
        "composition": args.composition,
        "reel": reel_name,
        "active_horizontal_pixels": DCDM_WIDTH,
        "active_vertical_pixels": DCDM_HEIGHT,
        "source_dimensions": [width, height],
        "source_frame_rate": source_fps,
        "dcdm_frame_rate": 24,
        "frame_count": args.frames,
        "colour_components": "SMPTE ST 428-1 X' Y' Z'",
        "reference_luminance_cd_m2": 48.0,
        "encoding_peak_cd_m2": 52.37,
        "transfer": "CV=round(4095*(48*XYZ/52.37)^(1/2.6))",
        "pixel_storage": (
            "12-bit unsigned code in the most significant 12 bits of each "
            "16-bit nominal TIFF RGB word; low four bits zero"
        ),
        "tiff": "TIFF 6.0, uncompressed, first pixel upper left, active pixels only",
        "files": files,
        "timing": {
            "total_wall_seconds": time.perf_counter() - started,
            "mean_seconds_per_frame": float(np.mean(durations)),
            "median_seconds_per_frame": float(np.median(durations)),
        },
        "references": [
            "SMPTE ST 428-1:2019",
            "DCI Digital Cinema System Specification section 3.2.2",
        ],
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
