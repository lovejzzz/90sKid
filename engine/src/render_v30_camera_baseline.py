#!/usr/bin/env python3
"""Render an official Panasonic V-709 camera baseline without film emulation."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

import emulsion_experiment as e
from render_v23_dual_masters import save_still, sha256


DEFAULT_V709_LUT = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "panasonic_v709"
    / "VLog_to_V709_forV35_ver100.cube"
)
EXPECTED_V709_SHA256 = "f99223675b29933952da2153bdb3137dd749d12964d0753db85e47576ca4578d"
V709_LEGAL_BLACK = np.float32(64.0 / 1024.0)
V709_LEGAL_WHITE = np.float32(940.0 / 1024.0)


def load_cube(path: Path) -> np.ndarray:
    if sha256(path) != EXPECTED_V709_SHA256:
        raise ValueError("Panasonic V-709 LUT integrity check failed")
    size: int | None = None
    values: list[list[float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("LUT_3D_SIZE"):
            size = int(stripped.split()[1])
            continue
        if stripped.startswith(("TITLE", "DOMAIN_", "LUT_1D_SIZE")):
            continue
        fields = stripped.split()
        if len(fields) == 3:
            values.append([float(value) for value in fields])
    if size is None or len(values) != size**3:
        raise ValueError("invalid Panasonic V-709 cube")
    return np.asarray(values, dtype=np.float32).reshape(size, size, size, 3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--v709-lut", type=Path, default=DEFAULT_V709_LUT)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    width, height, fps = e.probe_video(args.input)
    master = args.output / "05_camera_baseline_prores4444.mov"
    encoder = subprocess.Popen(
        e.prores_encoder_command(master, width, height, fps),
        stdin=subprocess.PIPE,
    )
    decoder = subprocess.Popen(
        [str(args.decoder), str(args.input), str(args.start_frame), str(args.frames)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert decoder.stdout is not None
    assert encoder.stdin is not None
    lut = load_cube(args.v709_lut)
    frame_bytes = width * height * 3 * 4
    representative_index = args.frames // 2
    representative: np.ndarray | None = None
    frame_times: list[float] = []
    started = time.perf_counter()
    processed = 0
    while processed < args.frames:
        mark = time.perf_counter()
        payload = decoder.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            break
        raw = np.frombuffer(payload, dtype="<f4").reshape(height, width, 3)
        exposed = raw * np.float32(2.0**args.exposure_stops)
        vgamut = e.bt2020_to_panasonic_vgamut(exposed)
        vlog = e.vlog_encode(vgamut)
        legal_encoded = e.apply_rgb_cube_lut(vlog, lut)
        # Panasonic's cube explicitly emits video-legal V-709. Our ProRes
        # encoder accepts full-range RGB and performs the RGB-to-legal-YUV
        # mapping itself, so normalize 10-bit codes 64–940 exactly once here.
        encoded = np.clip(
            (legal_encoded - V709_LEGAL_BLACK)
            / (V709_LEGAL_WHITE - V709_LEGAL_BLACK),
            0.0,
            1.0,
        )
        encoder.stdin.write(
            np.rint(encoded * 65535.0).astype("<u2").tobytes()
        )
        if processed == representative_index:
            representative = encoded.copy()
        processed += 1
        frame_times.append(time.perf_counter() - mark)
        elapsed = time.perf_counter() - started
        eta = elapsed / processed * (args.frames - processed)
        print(
            f"V30 Panasonic V-709 baseline frame {processed}/{args.frames} · "
            f"elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
            flush=True,
        )

    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError("ProRes RAW decoder failed")
    if processed != args.frames:
        raise RuntimeError(f"decoded {processed} frames; expected {args.frames}")
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("camera baseline encoder failed")
    e.finalize_prores_rec709_metadata(master)
    if representative is None:
        raise RuntimeError("representative frame was not captured")
    save_still(args.output / "still_camera_baseline.jpg", representative, "camera")

    total_seconds = time.perf_counter() - started
    timing = {
        "release": "V30 Panasonic V-709 camera baseline",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "input_decode": "AVFoundation extended-linear BT.2020/D65 ProRes RAW conversion",
        "display_transform": "linear BT.2020 to V-Gamut; Panasonic V-Log to V-709 official 3D LUT; legal 64–940 normalized once for RGB-to-ProRes encoding",
        "film_pipeline": "none",
        "creative_grade": "none",
        "exposure_stops": args.exposure_stops,
        "v709_lut": str(args.v709_lut),
        "v709_lut_sha256": EXPECTED_V709_SHA256,
        "frames": processed,
        "dimensions": [width, height],
        "fps": fps,
        "total_wall_seconds": total_seconds,
        "mean_seconds_per_frame": float(np.mean(frame_times)),
        "median_seconds_per_frame": float(np.median(frame_times)),
        "output": str(master),
    }
    (args.output / "timing.json").write_text(
        json.dumps(timing, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
