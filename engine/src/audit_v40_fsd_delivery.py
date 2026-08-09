#!/usr/bin/env python3
"""Release gate for the V40 FSD and deterministic comparison movies."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from audit_v40_motion_colour_grain import MOVIE, measure_movie


BRANCHES = ("fsd", "deterministic")


def probe(path: Path) -> dict[str, object]:
    return json.loads(subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries",
            (
                "stream=width,height,nb_frames,pix_fmt,profile,bits_per_raw_sample,"
                "color_space,color_transfer,color_primaries"
            ),
            "-of", "json", str(path),
        ],
        text=True,
    ))["streams"][0]


def metadata_gate(metadata: dict[str, object], companion: bool) -> dict[str, bool]:
    return {
        "width_5760": int(metadata.get("width", 0)) == 5760,
        "height_4320": int(metadata.get("height", 0)) == 4320,
        "frames_24": int(metadata.get("nb_frames", 0)) == 24,
        "pixel_format_12bit_444": metadata.get("pix_fmt") == "yuv444p12le",
        "bits_12": str(metadata.get("bits_per_raw_sample")) == "12",
        "profile_xq": metadata.get("profile") == "XQ",
        "primaries_bt709": metadata.get("color_primaries") == "bt709",
        "matrix_bt709": metadata.get("color_space") == "bt709",
        "transfer_expected": metadata.get("color_transfer") == (
            "iec61966-2-1" if companion else "bt709"
        ),
    }


def discrete_gate(rows: list[dict[str, object]], threshold: float, limit: float) -> bool:
    key = f"isolated_impulses_gt_{threshold:.2f}_count"
    return all(
        int(row[key])
        <= int(np.ceil(int(row["dark_pixel_count"]) * limit / 1e6))
        for row in rows
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--scenes", nargs="+", default=["T002", "T007", "T031"])
    parser.add_argument("--profile", default="V40")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report: dict[str, object] = {
        "audit": f"{args.profile} FSD/deterministic native every-frame delivery gate",
        "valid_domain": "two-pixel observer support perimeter excluded",
        "scenes": {},
    }
    passed = True
    for scene in args.scenes:
        scene_record: dict[str, object] = {}
        for branch in BRANCHES:
            directory = args.root / scene / branch
            companion = directory / MOVIE
            master = directory / "05_emulsion_master_prores4444.mov"
            companion_meta = probe(companion)
            master_meta = probe(master)
            companion_gates = metadata_gate(companion_meta, True)
            master_gates = metadata_gate(master_meta, False)
            motion = measure_movie(companion, 24)
            rows = motion["frames"]
            tail_gates = {
                "median_p9999_le_0_05": motion["worst"]["median_opponent_p9999"] <= 0.05,
                "isolated_gt_0_06_le_5_per_million": discrete_gate(rows, 0.06, 5.0),
                "isolated_gt_0_08_le_1_per_million": discrete_gate(rows, 0.08, 1.0),
            }
            contract_record: dict[str, object] | None = None
            contract_gates: dict[str, bool] = {}
            if branch == "fsd":
                contract_record = json.loads(
                    (directory / "manifest.json").read_text(encoding="utf-8")
                )
                contract = contract_record["fsd_contract"]
                frame_stats = contract_record["fsd_frame_stats"]
                absolute_frames = [int(row["absolute_frame"]) for row in frame_stats]
                contract_gates = {
                    "fsd_site_count_176": int(contract["site_count"]) == 176,
                    "fsd_sigma_0_597": abs(float(contract["correlation_sigma_native_px"]) - 0.597) < 1e-12,
                    "fsd_post_observer_signal_domain": contract.get("density_domain") == f"IEC 61966-2-1 signal after the deterministic {args.profile} observer",
                    "fsd_24_unique_absolute_frames": len(frame_stats) == 24 and len(set(absolute_frames)) == 24,
                    "fsd_gamut_constraint_fraction_le_0_03": max(float(row["gamut_luma_constraint_fraction"]) for row in frame_stats) <= 0.03,
                }
            gates = {
                **{f"master_{key}": value for key, value in master_gates.items()},
                **{f"companion_{key}": value for key, value in companion_gates.items()},
                **tail_gates,
                **contract_gates,
            }
            branch_pass = all(gates.values())
            passed &= branch_pass
            scene_record[branch] = {
                "master_metadata": master_meta,
                "companion_metadata": companion_meta,
                "motion": motion,
                "contract": contract_record,
                "gates": gates,
                "pass": branch_pass,
            }
        report["scenes"][scene] = scene_record
    report["all_gates_pass"] = passed
    output = args.output or args.root / f"{args.profile.lower()}_fsd_delivery_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
