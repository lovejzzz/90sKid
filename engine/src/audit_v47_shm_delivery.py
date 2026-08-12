#!/usr/bin/env python3
"""Delivery metadata and colour-impulse gates for the V47 SHM movie."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from audit_v40_motion_colour_grain import measure_movie


BRANCHES = ("shm_projection", "shm_scan")


def probe(path: Path) -> dict[str, object]:
    return json.loads(
        subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries",
                "stream=width,height,nb_frames,pix_fmt,profile,bits_per_raw_sample,color_space,color_transfer,color_primaries",
                "-of", "json", str(path),
            ],
            text=True,
        )
    )["streams"][0]


def metadata_gates(row: dict[str, object], transfer: str) -> dict[str, bool]:
    return {
        "native_5760x4320": [int(row.get("width", 0)), int(row.get("height", 0))]
        == [5760, 4320],
        "twenty_four_frames": int(row.get("nb_frames", 0)) == 24,
        "prores_4444_xq": row.get("profile") == "XQ",
        "twelve_bit_444": row.get("pix_fmt") == "yuv444p12le"
        and str(row.get("bits_per_raw_sample")) == "12",
        "rec709_primaries_and_matrix": row.get("color_primaries") == "bt709"
        and row.get("color_space") == "bt709",
        "expected_transfer": row.get("color_transfer") == transfer,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report: dict[str, object] = {
        "audit": "V47 SHM encoded delivery",
        "branches": {},
    }
    passed = True
    for branch in BRANCHES:
        root = args.root / branch
        master = root / "05_emulsion_master_prores4444.mov"
        companion = root / "06_quicktime_preview_srgb_prores4444.mov"
        master_meta = probe(master)
        companion_meta = probe(companion)
        motion = measure_movie(companion, 24)
        tail = motion["worst"]
        gates = {
            **{f"master_{key}": value for key, value in metadata_gates(master_meta, "bt709").items()},
            **{f"companion_{key}": value for key, value in metadata_gates(companion_meta, "iec61966-2-1").items()},
            "no_isolated_opponent_gt_0_08": all(
                int(row["isolated_impulses_gt_0.08_count"]) == 0
                for row in motion["frames"]
            ),
            "median_opponent_p9999_le_0_05": float(tail["median_opponent_p9999"]) <= 0.05,
        }
        branch_pass = all(gates.values())
        passed &= branch_pass
        report["branches"][branch] = {
            "master_metadata": master_meta,
            "companion_metadata": companion_meta,
            "motion_colour_impulse": motion,
            "gates": gates,
            "pass": branch_pass,
        }
    report["all_gates_pass"] = passed
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
