#!/usr/bin/env python3
"""Release gate for the four-view V43H Hypothesis Edition delivery."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import numpy as np

from audit_v40_motion_colour_grain import MOVIE, measure_movie


BRANCHES = {
    "projection": ("projection", "05_emulsion_master_prores4444.mov", True),
    "scan": ("bluray_scan", "05_emulsion_master_prores4444.mov", True),
    "fsd": ("fsd", "05_emulsion_master_prores4444.mov", True),
    "camera": ("camera_baseline", "05_camera_baseline_prores4444.mov", False),
}

# Two tail thresholds are tested on 24 frames, three stochastic branches and
# three scenes.  A raw ``count <= ceil(expected_count)`` gate rejects a safe
# Poisson process about half the time whenever its count lands just above the
# mean.  Use a one-sided Bonferroni boundary so the probability of *any* false
# release failure across this complete family stays below one percent.  V39's
# failed primary-colour field exceeded these limits by orders of magnitude.
DISCRETE_TEST_FAMILY = 2 * 24 * 3 * 3
DISCRETE_FAMILYWISE_ALPHA = 0.01


def poisson_upper_count(mean: float, tail_probability: float) -> int:
    """Smallest count whose cumulative Poisson probability reaches 1-alpha."""
    if mean < 0.0 or not 0.0 < tail_probability < 1.0:
        raise ValueError("invalid Poisson gate parameters")
    probability = math.exp(-mean)
    cumulative = probability
    count = 0
    target = 1.0 - tail_probability
    while cumulative < target:
        count += 1
        probability *= mean / count
        cumulative += probability
    return count


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict[str, object]:
    return json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                (
                    "stream=width,height,nb_frames,pix_fmt,profile,bits_per_raw_sample,"
                    "color_space,color_transfer,color_primaries"
                ),
                "-of",
                "json",
                str(path),
            ],
            text=True,
        )
    )["streams"][0]


def metadata_gates(metadata: dict[str, object], companion: bool) -> dict[str, bool]:
    return {
        "width_5760": int(metadata.get("width", 0)) == 5760,
        "height_4320": int(metadata.get("height", 0)) == 4320,
        "frames_24": int(metadata.get("nb_frames", 0)) == 24,
        "pixel_format_12bit_444": metadata.get("pix_fmt") == "yuv444p12le",
        "bits_12": str(metadata.get("bits_per_raw_sample")) == "12",
        "profile_xq": metadata.get("profile") == "XQ",
        "primaries_bt709": metadata.get("color_primaries") == "bt709",
        "matrix_bt709": metadata.get("color_space") == "bt709",
        "transfer_expected": metadata.get("color_transfer")
        == ("iec61966-2-1" if companion else "bt709"),
    }


def discrete_gate(
    rows: list[dict[str, object]], threshold: float, limit_per_million: float
) -> bool:
    key = f"isolated_impulses_gt_{threshold:.2f}_count"
    per_test_alpha = DISCRETE_FAMILYWISE_ALPHA / DISCRETE_TEST_FAMILY
    return all(
        int(row[key])
        <= poisson_upper_count(
            int(row["dark_pixel_count"]) * limit_per_million / 1_000_000,
            per_test_alpha,
        )
        for row in rows
    )


def audit_branch(scene_root: Path, branch: str) -> dict[str, object]:
    directory_name, master_name, grain_gate = BRANCHES[branch]
    directory = scene_root / directory_name
    master = directory / master_name
    companion = directory / MOVIE
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    master_meta = probe(master)
    companion_meta = probe(companion)
    gates = {
        **{f"master_{key}": value for key, value in metadata_gates(master_meta, False).items()},
        **{f"companion_{key}": value for key, value in metadata_gates(companion_meta, True).items()},
        "release_class_is_hypothesis": manifest.get("release_class")
        == "hypothesis_not_measurement",
        "profile_is_v43h": manifest.get("engine", {}).get("profile") == "v43h",
        "manifest_branch_matches": manifest.get("branch")
        == ("camera" if branch == "camera" else directory_name),
        "master_hash_matches": manifest.get("master_sha256") == sha256(master),
        "companion_hash_matches": manifest.get("companion_sha256")
        == sha256(companion),
    }
    motion: dict[str, object] | None = measure_movie(companion, 24)
    tone_rows = motion["frames"]
    tone = {
        key: {
            "minimum_across_frames": min(float(row[key]) for row in tone_rows),
            "maximum_across_frames": max(float(row[key]) for row in tone_rows),
        }
        for key in (
            "luma_p001",
            "luma_p01",
            "luma_p50",
            "luma_p99",
            "luma_p999",
            "display_black_fraction",
            "display_white_fraction",
        )
    }
    if grain_gate:
        rows = motion["frames"]
        worst = motion["worst"]
        gates.update(
            {
                "median_opponent_p9999_le_0_05": worst["median_opponent_p9999"]
                <= 0.05,
                "isolated_gt_0_06_poisson_fwer_1pct_at_5_per_million": discrete_gate(
                    rows, 0.06, 5.0
                ),
                "isolated_gt_0_08_poisson_fwer_1pct_at_1_per_million": discrete_gate(
                    rows, 0.08, 1.0
                ),
            }
        )
    if branch == "projection":
        sampler = manifest["sampler_audit"]
        gates.update(
            {
                "sampler_45_calls_per_frame": sampler.get("calls_per_frame") == 45,
                "sampler_24_frames": sampler.get("frames_audited") == 24,
                "sampler_no_duplicate_identity": sampler.get(
                    "duplicate_identity_count"
                )
                == 0,
            }
        )
    if branch == "fsd":
        stats = manifest.get("fsd_frame_stats", [])
        frames = [int(row["absolute_frame"]) for row in stats]
        gates.update(
            {
                "fsd_is_independent_pipeline": manifest["fsd_contract"].get(
                    "independent_pipeline"
                )
                is True,
                "fsd_24_unique_absolute_frames": len(stats) == 24
                and len(set(frames)) == 24,
                "fsd_gamut_constraint_fraction_le_0_03": max(
                    float(row["gamut_luma_constraint_fraction"]) for row in stats
                )
                <= 0.03,
            }
        )
    return {
        "master_metadata": master_meta,
        "companion_metadata": companion_meta,
        "tone_and_clip_summary": tone,
        "motion_colour_grain": motion,
        "gates": gates,
        "pass": all(gates.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--scenes", nargs="+", default=["T020", "T032", "T007"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "audit": "V43H four-view native-resolution release gate",
        "interpretation": (
            "Passing means the hypothetical experiment is internally consistent; "
            "it does not turn unmeasured V43H parameters into measured 5279 facts."
        ),
        "scenes": {},
    }
    passed = True
    for scene in args.scenes:
        record = {
            branch: audit_branch(args.root / scene, branch)
            for branch in BRANCHES
        }
        report["scenes"][scene] = record
        passed &= all(bool(item["pass"]) for item in record.values())
    report["all_gates_pass"] = passed
    output = args.output or args.root / "v43h_release_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
