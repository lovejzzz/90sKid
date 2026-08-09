#!/usr/bin/env python3
"""Verify the current encoded-signal to 12-bit ProRes legal-range boundary."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

import emulsion_experiment as e


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1024, 64
    ramp = np.linspace(0.0, 1.0, width, dtype=np.float32)
    image = np.repeat(ramp[None, :, None], height, axis=0)
    image = np.repeat(image, 3, axis=2)
    source_u16 = np.rint(image * 65535.0).astype("<u2")
    path = args.output_dir / "rec709_signal_ramp_prores4444.mov"
    encoder = subprocess.Popen(
        e.prores_encoder_command(path, width, height, "24000/1001"),
        stdin=subprocess.PIPE,
    )
    assert encoder.stdin is not None
    encoder.stdin.write(source_u16.tobytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("ProRes ramp encode failed")
    e.finalize_prores_rec709_metadata(path)
    decoded = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1",
            "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    output = (
        np.frombuffer(decoded, dtype="<u2")
        .reshape(height, width, 3)
        .astype(np.float32)
        / 65535.0
    )
    error = output - image
    report = {
        "mean_abs_signal_error": float(np.mean(np.abs(error))),
        "p99_abs_signal_error": float(np.quantile(np.abs(error), 0.99)),
        "max_abs_signal_error": float(np.max(np.abs(error))),
        "decoded_black": output[0, 0].tolist(),
        "decoded_middle": output[0, width // 2].tolist(),
        "decoded_white": output[0, -1].tolist(),
        "expected_metadata": "12-bit ProRes 4444, tv range, Rec.709 1-1-1",
    }
    (args.output_dir / "prores_roundtrip_metrics.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
