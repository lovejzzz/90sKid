#!/usr/bin/env python3
"""Native metadata, tone and colour-tail gates for the V45 three-scene release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_v40_motion_colour_grain import measure_movie
from audit_v43h_release import metadata_gates, poisson_upper_count, probe


BRANCHES = {"projection": "projection", "scan": "bluray_scan"}
LATTICE_SHA256 = "28ac498942c7ddc923fa3b988b8dd6663266026893f96a744b59c8090bfd3cf7"
FAMILYWISE_ALPHA = 0.01
TEST_FAMILY = 2 * 24 * 2 * 3


def discrete_gate(
    rows: list[dict[str, object]], threshold: float, limit_per_million: float
) -> bool:
    key = f"isolated_impulses_gt_{threshold:.2f}_count"
    alpha = FAMILYWISE_ALPHA / TEST_FAMILY
    return all(
        int(row[key])
        <= poisson_upper_count(
            int(row["dark_pixel_count"]) * limit_per_million / 1_000_000,
            alpha,
        )
        for row in rows
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--scenes", nargs="+", default=["T020", "T032", "T007"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "audit": "V45 official-observer native release gate",
        "familywise_false_rejection_rate": FAMILYWISE_ALPHA,
        "scenes": {},
    }
    passed = True
    for scene in args.scenes:
        timing = json.loads((args.root / scene / "timing.json").read_text())
        scene_record: dict[str, object] = {}
        scene_common = {
            "profile_v45": timing["engine"].get("profile") == "v45",
            "official_cie_lattice": timing["engine"].get("print_lattice_sha256")
            == LATTICE_SHA256,
            "research_conformance": timing["engine"]["research_conformance"].get(
                "image_model_conformant"
            )
            is True,
            "archive_exact_reference": timing["config"].get("mode")
            == "archive_exact_cpu",
        }
        for branch, directory in BRANCHES.items():
            root = args.root / scene / directory
            master_meta = probe(root / "05_emulsion_master_prores4444.mov")
            companion = root / "06_quicktime_preview_srgb_prores4444.mov"
            companion_meta = probe(companion)
            review_meta = probe(root / "07_scale_integrated_review_srgb_prores4444.mov")
            motion = measure_movie(companion, 24)
            rows = motion["frames"]
            worst = motion["worst"]
            gates = {
                **scene_common,
                **{f"master_{key}": value for key, value in metadata_gates(master_meta, False).items()},
                **{f"companion_{key}": value for key, value in metadata_gates(companion_meta, True).items()},
                "review_width_1920": int(review_meta.get("width", 0)) == 1920,
                "review_height_1440": int(review_meta.get("height", 0)) == 1440,
                "review_frames_24": int(review_meta.get("nb_frames", 0)) == 24,
                "review_12bit_444": review_meta.get("pix_fmt") == "yuv444p12le",
                "review_srgb": review_meta.get("color_transfer") == "iec61966-2-1",
                "median_opponent_p9999_le_0_05": worst["median_opponent_p9999"] <= 0.05,
                "isolated_gt_0_06_poisson_fwer": discrete_gate(rows, 0.06, 5.0),
                "isolated_gt_0_08_poisson_fwer": discrete_gate(rows, 0.08, 1.0),
            }
            if branch == "projection":
                gates["dark_opponent_p9999_le_0_035"] = (
                    worst["dark_opponent_p9999"] <= 0.035
                )
                gates["opponent_to_luma_le_0_20"] = (
                    worst["visible_chroma_to_luma_highpass_rms"] <= 0.20
                )
            branch_pass = all(gates.values())
            passed &= branch_pass
            scene_record[branch] = {
                "master_metadata": master_meta,
                "companion_metadata": companion_meta,
                "review_metadata": review_meta,
                "motion_colour_grain": motion,
                "gates": gates,
                "pass": branch_pass,
            }
        report["scenes"][scene] = scene_record
    report["all_gates_pass"] = passed
    output = args.output or args.root / "v45_release_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
