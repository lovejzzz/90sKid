#!/usr/bin/env python3
"""Validate corrected V25 Rec.709 masters against the accepted V24 signal."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


MASTER = "05_emulsion_master_prores4444.mov"
CLIPS = ("T020", "T032")
BRANCHES = ("projection", "bluray_scan")


def probe(path: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries",
            "stream=width,height,nb_frames,pix_fmt,bits_per_raw_sample,color_space,color_transfer,color_primaries",
            "-of", "json", str(path),
        ],
        text=True,
    )
    return json.loads(payload)["streams"][0]


def first_frame_signal(path: Path) -> dict[str, float]:
    output = subprocess.check_output(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
            "-vf", "select=eq(n\\,0),signalstats,metadata=print:file=-",
            "-frames:v", "1", "-f", "null", "-",
        ],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    return {
        name: float(value)
        for name, value in re.findall(r"lavfi\.signalstats\.(YAVG|YLOW)=([0-9.]+)", output)
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("corrected", type=Path)
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()
    results: dict[str, object] = {}
    for clip in CLIPS:
        for branch in BRANCHES:
            key = f"{clip}/{branch}"
            current = args.corrected / clip / branch / MASTER
            reference = args.baseline / clip / branch / MASTER
            metadata = probe(current)
            expected = {
                "width": 5760, "height": 4320, "nb_frames": "24",
                "pix_fmt": "yuv444p12le", "bits_per_raw_sample": "12",
                "color_space": "bt709", "color_transfer": "bt709",
                "color_primaries": "bt709",
            }
            for field, value in expected.items():
                if metadata.get(field) != value:
                    raise RuntimeError(f"{key}: {field}={metadata.get(field)!r}, expected {value!r}")
            signal = first_frame_signal(current)
            baseline = first_frame_signal(reference)
            deltas = {name: signal[name] - baseline[name] for name in ("YAVG", "YLOW")}
            if abs(deltas["YAVG"]) > 2.0 or abs(deltas["YLOW"]) > 3.0:
                raise RuntimeError(f"{key}: brightness regression {deltas}")
            results[key] = {"metadata": metadata, "signal": signal, "v24_delta": deltas}
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
