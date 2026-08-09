#!/usr/bin/env python3
"""Validate V27 delivery invariants against V26 and the neutral-scale diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


MASTER = "05_emulsion_master_prores4444.mov"
CLIPS = ("T020", "T032")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict[str, object]:
    payload = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height,nb_frames,pix_fmt,bits_per_raw_sample,color_space,color_transfer,color_primaries",
        "-of", "json", str(path),
    ], text=True)
    return json.loads(payload)["streams"][0]


def frame_signals(path: Path) -> list[dict[str, float]]:
    output = subprocess.check_output([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
        "-vf", "signalstats,metadata=print:file=-", "-f", "null", "-",
    ], text=True, stderr=subprocess.DEVNULL)
    frames: list[dict[str, float]] = []
    current: dict[str, float] = {}
    for line in output.splitlines():
        if line.startswith("frame:"):
            if current:
                frames.append(current)
            current = {}
            continue
        match = re.match(r"lavfi\.signalstats\.(YMIN|YLOW|YAVG|YMAX)=([0-9.]+)", line)
        if match:
            current[match.group(1)] = float(match.group(2))
    if current:
        frames.append(current)
    return frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("v27_root", type=Path)
    parser.add_argument("v26_root", type=Path)
    parser.add_argument("diagnostic", type=Path)
    args = parser.parse_args()

    diagnostic = json.loads(args.diagnostic.read_text(encoding="utf-8"))
    if diagnostic["after"]["maximum_neutral_channel_residual"] > 0.0025:
        raise RuntimeError("neutral-axis maximum residual exceeds V27 gate")
    if diagnostic["after"]["maximum_absolute_green_opponent"] > 0.0025:
        raise RuntimeError("green-opponent maximum residual exceeds V27 gate")
    if diagnostic["maximum_absolute_luma_drift"] > 2e-7:
        raise RuntimeError("neutral diagnostic luminance drift exceeds V27 gate")
    if diagnostic["maximum_absolute_projection_drift"] != 0.0:
        raise RuntimeError("projection diagnostic drift is nonzero")

    expected = {
        "width": 5760, "height": 4320, "nb_frames": "24",
        "pix_fmt": "yuv444p12le", "bits_per_raw_sample": "12",
        "color_space": "bt709", "color_transfer": "bt709",
        "color_primaries": "bt709",
    }
    results: dict[str, object] = {"neutral_scale": diagnostic}
    for clip in CLIPS:
        v27_projection = args.v27_root / clip / "projection" / MASTER
        v26_projection = args.v26_root / clip / "projection" / MASTER
        if sha256(v27_projection) != sha256(v26_projection):
            raise RuntimeError(f"{clip}: projection is not byte-identical to V26")

        current = args.v27_root / clip / "bluray_scan" / MASTER
        reference = args.v26_root / clip / "bluray_scan" / MASTER
        metadata = probe(current)
        for field, value in expected.items():
            if metadata.get(field) != value:
                raise RuntimeError(f"{clip}: {field}={metadata.get(field)!r}, expected {value!r}")
        current_signals = frame_signals(current)
        reference_signals = frame_signals(reference)
        if len(current_signals) != 24 or len(reference_signals) != 24:
            raise RuntimeError(f"{clip}: expected 24 signal-stat frames")
        deltas = {
            field: [a[field] - b[field] for a, b in zip(current_signals, reference_signals)]
            for field in ("YMIN", "YLOW", "YAVG", "YMAX")
        }
        if max(abs(value) for value in deltas["YAVG"]) > 0.5:
            raise RuntimeError(f"{clip}: encoded YAVG drift exceeds 0.5 / 4095")
        if max(abs(value) for value in deltas["YLOW"]) > 1.0:
            raise RuntimeError(f"{clip}: encoded YLOW drift exceeds 1 / 4095")
        if max(frame["YMAX"] for frame in current_signals) >= 4095:
            raise RuntimeError(f"{clip}: luma clipping detected")
        results[clip] = {
            "metadata": metadata,
            "projection_sha256": sha256(v27_projection),
            "maximum_absolute_signal_delta": {
                field: max(abs(value) for value in values)
                for field, values in deltas.items()
            },
            "v27_luma_range": {
                "minimum_code": min(frame["YMIN"] for frame in current_signals),
                "maximum_code": max(frame["YMAX"] for frame in current_signals),
            },
        }
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
