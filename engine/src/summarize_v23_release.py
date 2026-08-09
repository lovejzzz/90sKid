#!/usr/bin/env python3
"""Combine two independently timed source renders for one release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release_root", type=Path)
    parser.add_argument("--release", default="V23")
    args = parser.parse_args()

    timings = {
        name: json.loads((args.release_root / name / "timing.json").read_text())
        for name in ("T020", "T032")
    }
    manifests = {
        name: json.loads(
            (args.release_root / name / "projection" / "manifest.json").read_text()
        )
        for name in ("T020", "T032")
    }
    concurrent_wall = max(
        item["total_wall_seconds_including_hashes"] for item in timings.values()
    )
    serial_work = sum(
        item["total_wall_seconds_including_hashes"] for item in timings.values()
    )
    source_seconds = sum(item["rendered_source_seconds"] for item in timings.values())
    report = {
        "release": args.release,
        "execution": "two source jobs launched concurrently; each job emits projection and scan from one shared emulsion",
        "sources": timings,
        "combined": {
            "output_masters": 4,
            "source_clips": 2,
            "frames_per_source": {
                name: manifest["frames_processed"] for name, manifest in manifests.items()
            },
            "total_source_seconds": source_seconds,
            "approximate_concurrent_wall_seconds": concurrent_wall,
            "approximate_concurrent_wall_minutes": concurrent_wall / 60.0,
            "sum_of_per_source_wall_seconds": serial_work,
            "sum_of_per_source_wall_hours": serial_work / 3600.0,
            "concurrent_wall_seconds_per_combined_source_second": concurrent_wall / source_seconds,
        },
    }
    (args.release_root / "release_timing.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report["combined"], indent=2))


if __name__ == "__main__":
    main()
