#!/usr/bin/env python3
"""Rejected P3-D65/gamma-2.6 ProRes transport probe.

The colour math is retained for reproducibility, but V32 does not release this
as an industry-standard cinema master: ProRes frame/container signalling cannot
unambiguously express this RGB monitoring contract across players.  Production
V32 uses ``build_v32_dcdm_reference.py`` instead.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

import emulsion_experiment as e
from apply_v31_normal_process_adapter import rec709_decode
from render_v23_dual_masters import sha256


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frames", type=int, default=24)
    args = parser.parse_args()
    width, height, fps = e.probe_video(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(args.input), "-an",
            "-frames:v", str(args.frames), "-pix_fmt", "rgb48le",
            "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    encoder = subprocess.Popen(
        e.prores_p3d65_gamma26_encoder_command(
            args.output, width, height, fps
        ),
        stdin=subprocess.PIPE,
    )
    assert decoder.stdout is not None and encoder.stdin is not None
    frame_bytes = width * height * 3 * 2
    durations: list[float] = []
    started = time.perf_counter()
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
        linear_rec709 = rec709_decode(signal)
        linear_p3 = e.linear_rec709_to_p3_d65(linear_rec709)
        encoded_p3 = e.gamma26_encode(linear_p3)
        encoder.stdin.write(
            np.rint(encoded_p3 * 65535.0).astype("<u2").tobytes()
        )
        durations.append(time.perf_counter() - mark)
        print(
            f"V32 P3-D65 reference frame {frame + 1}/{args.frames} · "
            f"{durations[-1]:.2f}s",
            flush=True,
        )
    decoder.stdout.close()
    encoder.stdin.close()
    if decoder.wait() or encoder.wait():
        raise RuntimeError("P3-D65 reference transcode failed")
    e.finalize_prores_metadata(args.output, "smpte432", "smpte428", "bt709")
    manifest = {
        "release": "V32 measurement-first cinema-monitor reference",
        "source": str(args.input),
        "source_sha256": sha256(args.input),
        "output": str(args.output),
        "output_sha256": sha256(args.output),
        "frames": args.frames,
        "dimensions": [width, height],
        "fps": fps,
        "colour": {
            "source": "Rec.709-D65 OETF 1-1-1",
            "decode": "inverse Rec.709 OETF to linear Rec.709-D65",
            "matrix": "linear Rec.709-D65 -> XYZ-D65 -> P3-D65",
            "encoding": "gamma 2.6 cinema-monitor reference",
            "primaries": "SMPTE EG 432-1 P3-D65 (smpte432)",
            "transfer_tag": "SMPTE ST 428 family (smpte428 MOV nclx)",
            "matrix_tag": "BT.709 YCbCr transport only",
            "scope": "appearance-preserving review master, not a DCP or new film look",
        },
        "timing": {
            "total_wall_seconds": time.perf_counter() - started,
            "mean_seconds_per_frame": float(np.mean(durations)),
            "median_seconds_per_frame": float(np.median(durations)),
        },
    }
    (args.output.parent / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
