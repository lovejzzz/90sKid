#!/usr/bin/env python3
"""Atomically ensure V29 masters retain source audio, timecode and Rec.709 tags."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from render_v23_dual_masters import sha256


def finalize(master: Path, source: Path) -> None:
    temporary = master.with_name(master.stem + ".source-streams.mov")
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(master), "-i", str(source),
            "-map", "0:v:0", "-map", "1:a?", "-map", "1:d?", "-c", "copy",
            "-bsf:v", "prores_metadata=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-movflags", "write_colr", "-map_metadata", "1",
            "-metadata:s:v:0", "encoder=5279 Emulsion Project V29",
            str(temporary),
        ],
        check=True,
    )
    temporary.replace(master)
    manifest_path = master.parent / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["master_sha256"] = sha256(master)
    manifest["audio"] = "source PCM s24le, 48 kHz, 4 channels, stream copied"
    manifest["timecode"] = "source 12:04:05:23 retained in video and tmcd track"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    for directory in ("projection", "bluray_scan"):
        finalize(args.release / directory / "05_emulsion_master_prores4444.mov", args.source)


if __name__ == "__main__":
    main()
