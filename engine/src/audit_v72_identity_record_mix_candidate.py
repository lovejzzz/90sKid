#!/usr/bin/env python3
"""Native-scene gate for the V72 identity record-formation candidate.

V72 changes one operator only: the unidentified speed-population
``SUBEMULSION_DYE_RECORD_MIX`` is replaced by identity.  This audit compares
master-derived, scale-integrated review light against V66 on the outdoor T020
scene and the measured T003 DKC-Pro chart frame.  It does not fit the chart or
claim that identity is measured 5279 behaviour.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from audit_t003_colorchecker import PATCHES, patch_samples


MOVIE = "07_scale_integrated_review_srgb_prores4444.mov"
BRANCHES = ("projection", "bluray_scan")
T003_CORNERS_NATIVE = np.asarray(
    [[3500.0, 1635.0], [4330.0, 1565.0], [4390.0, 2188.0], [3510.0, 2230.0]],
    dtype=np.float32,
)
IDEAL_GRID = np.asarray([[0, 0], [6, 0], [6, 3], [0, 3]], dtype=np.float32)
LUMA = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float64)


def decode_srgb_review(path: Path) -> np.ndarray:
    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,nb_frames",
                "-of",
                "json",
                str(path),
            ],
            text=True,
        )
    )["streams"][0]
    width = int(probe["width"])
    height = int(probe["height"])
    payload = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-vf",
            "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
            "-pix_fmt",
            "rgb48le",
            "-f",
            "rawvideo",
            "-",
        ]
    )
    expected = width * height * 3 * 2
    if len(payload) != expected:
        raise RuntimeError(f"short review decode for {path}: {len(payload)} != {expected}")
    code = (
        np.frombuffer(payload, dtype="<u2")
        .reshape(height, width, 3)
        .astype(np.float32)
        / 65535.0
    )
    return np.where(
        code <= 0.04045,
        code / 12.92,
        ((code + 0.055) / 1.055) ** 2.4,
    ).astype(np.float32)


def image_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    difference = np.abs(candidate.astype(np.float64) - reference.astype(np.float64))
    reference_luma = np.einsum("...c,c->...", reference, LUMA)
    candidate_luma = np.einsum("...c,c->...", candidate, LUMA)
    luma_difference = np.abs(candidate_luma - reference_luma)
    midtone = (reference_luma >= 0.10) & (reference_luma <= 0.50)
    reference_lab = e.linear_rec709_to_oklab(reference)
    candidate_lab = e.linear_rec709_to_oklab(candidate)
    delta_lab = np.linalg.norm(candidate_lab - reference_lab, axis=-1)
    return {
        "linear_rgb_mae": float(np.mean(difference)),
        "linear_rgb_p95_absolute": float(np.percentile(difference, 95)),
        "linear_rgb_p99_absolute": float(np.percentile(difference, 99)),
        "linear_rgb_maximum_absolute": float(np.max(difference)),
        "oklab_delta_median": float(np.median(delta_lab)),
        "oklab_delta_p95": float(np.percentile(delta_lab, 95)),
        "oklab_delta_p99": float(np.percentile(delta_lab, 99)),
        "luma": {
            "reference_median": float(np.median(reference_luma)),
            "candidate_median": float(np.median(candidate_luma)),
            "median_ratio": float(
                np.median(candidate_luma) / max(np.median(reference_luma), 1.0e-12)
            ),
            "median_absolute_difference": float(np.median(luma_difference)),
            "p95_absolute_difference": float(np.percentile(luma_difference, 95)),
            "midtone_pixel_count": int(np.sum(midtone)),
            "midtone_median_ratio": float(
                np.median(candidate_luma[midtone])
                / max(np.median(reference_luma[midtone]), 1.0e-12)
            ),
            "reference_p99": float(np.percentile(reference_luma, 99)),
            "candidate_p99": float(np.percentile(candidate_luma, 99)),
            "reference_black_fraction": float(np.mean(reference_luma <= 0.0)),
            "candidate_black_fraction": float(np.mean(candidate_luma <= 0.0)),
            "reference_white_fraction": float(np.mean(reference_luma >= 1.0)),
            "candidate_white_fraction": float(np.mean(candidate_luma >= 1.0)),
        },
    }


def chart_patch_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    scale_x = reference.shape[1] / 5760.0
    scale_y = reference.shape[0] / 4320.0
    corners = T003_CORNERS_NATIVE * np.asarray([scale_x, scale_y], dtype=np.float32)
    homography = cv2.getPerspectiveTransform(IDEAL_GRID, corners)
    rows: list[dict[str, object]] = []
    for index, patch in enumerate(PATCHES):
        row, column = divmod(index, 6)
        reference_rgb = np.median(
            patch_samples(reference, homography, row, column), axis=0
        )
        candidate_rgb = np.median(
            patch_samples(candidate, homography, row, column), axis=0
        )
        labs = e.linear_rec709_to_oklab(
            np.asarray([[reference_rgb, candidate_rgb]], dtype=np.float32)
        )[0]
        chroma = np.linalg.norm(labs[:, 1:3], axis=1)
        hue = np.degrees(np.arctan2(labs[:, 2], labs[:, 1]))
        hue_delta = float((hue[1] - hue[0] + 180.0) % 360.0 - 180.0)
        rows.append(
            {
                "patch": index + 1,
                "name": patch[0],
                "reference_linear_rgb": reference_rgb.tolist(),
                "candidate_linear_rgb": candidate_rgb.tolist(),
                "oklab_delta": float(np.linalg.norm(labs[1] - labs[0])),
                "hue_delta_degrees": hue_delta,
                "chroma_ratio": float(chroma[1] / max(chroma[0], 1.0e-12)),
                "luma_ratio": float(
                    (candidate_rgb @ LUMA) / max(reference_rgb @ LUMA, 1.0e-12)
                ),
            }
        )

    neutral = rows[1:6]
    colour = rows[6:18]
    return {
        "patches": rows,
        "neutral_patches_2_to_6": {
            "maximum_oklab_delta": float(max(row["oklab_delta"] for row in neutral)),
            "median_luma_ratio": float(np.median([row["luma_ratio"] for row in neutral])),
            "maximum_absolute_luma_ratio_delta": float(
                max(abs(row["luma_ratio"] - 1.0) for row in neutral)
            ),
        },
        "colour_patches_7_to_18": {
            "median_absolute_hue_delta_degrees": float(
                np.median([abs(row["hue_delta_degrees"]) for row in colour])
            ),
            "maximum_absolute_hue_delta_degrees": float(
                max(abs(row["hue_delta_degrees"]) for row in colour)
            ),
            "median_chroma_ratio": float(
                np.median([row["chroma_ratio"] for row in colour])
            ),
            "minimum_chroma_ratio": float(min(row["chroma_ratio"] for row in colour)),
            "maximum_chroma_ratio": float(max(row["chroma_ratio"] for row in colour)),
        },
        "authority": (
            "paired V66/V72 transport diagnostic only; outdoor illumination and "
            "the manufacturer's Lab measurement illuminant remain unidentified"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--reference-grain", type=Path)
    parser.add_argument("--candidate-grain", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "audit": "V72 identity direct-record-mix native scene and chart gate",
        "reference_profile": "V66",
        "candidate_profile": "V72",
        "single_variable_change": (
            "replace the unidentified direct speed-population record-mix matrix "
            "with exact identity; retain sensitivity overlap, DIR, net dye/mask "
            "spectra, 2383 spectral printing and both delivery branches"
        ),
        "scenes": {},
    }
    scene_paths = {
        "T020": ("T020", "T020"),
        "T003_frame160": ("T003_frame160", "T003_frame160"),
    }
    for scene, (reference_scene, candidate_scene) in scene_paths.items():
        branches: dict[str, object] = {}
        for branch in BRANCHES:
            reference_path = args.reference / reference_scene / branch / MOVIE
            candidate_path = args.candidate / candidate_scene / branch / MOVIE
            reference = decode_srgb_review(reference_path)
            candidate = decode_srgb_review(candidate_path)
            branch_result: dict[str, object] = {
                "reference": str(reference_path),
                "candidate": str(candidate_path),
                "image_change": image_metrics(reference, candidate),
            }
            if scene == "T003_frame160":
                branch_result["chart"] = chart_patch_metrics(reference, candidate)
            branches[branch] = branch_result
        report["scenes"][scene] = branches

    gates: dict[str, object] = {}
    for scene, branches in report["scenes"].items():
        for branch, result in branches.items():
            prefix = f"{scene}_{branch}"
            metrics = result["image_change"]
            luma = metrics["luma"]
            # A whole-frame relative median is ill-conditioned when a scene's
            # median is in the deep toe (T003 is about 0.013 linear).  Gate the
            # absolute change there and use a relative comparison only on
            # visible 0.10--0.50 midtones.
            gates[f"{prefix}_median_luma_absolute_change_below_0.001"] = bool(
                luma["median_absolute_difference"] <= 0.001
            )
            gates[f"{prefix}_midtone_luma_ratio_within_1pct"] = bool(
                0.99 <= luma["midtone_median_ratio"] <= 1.01
            )
            gates[f"{prefix}_no_white_clip_increase"] = bool(
                luma["candidate_white_fraction"]
                <= luma["reference_white_fraction"] + 1.0e-6
            )
    for branch in BRANCHES:
        chart = report["scenes"]["T003_frame160"][branch]["chart"]
        gates[f"T003_{branch}_neutral_delta_below_0.01_oklab"] = bool(
            chart["neutral_patches_2_to_6"]["maximum_oklab_delta"] <= 0.01
        )
        gates[f"T003_{branch}_colour_hue_delta_below_2deg"] = bool(
            chart["colour_patches_7_to_18"]["maximum_absolute_hue_delta_degrees"]
            <= 2.0
        )
    if (args.reference_grain is None) != (args.candidate_grain is None):
        raise ValueError("both native colour-grain reports must be supplied together")
    if args.reference_grain is not None and args.candidate_grain is not None:
        reference_grain = json.loads(args.reference_grain.read_text(encoding="utf-8"))
        candidate_grain = json.loads(args.candidate_grain.read_text(encoding="utf-8"))
        paired: dict[str, object] = {
            "reference": str(args.reference_grain),
            "candidate": str(args.candidate_grain),
            "branches": {},
            "interpretation": (
                "The T020-derived absolute projection thresholds fail on both "
                "profiles because this chart/foliage frame contains many natural "
                "high-contrast chromatic edges. Paired same-seed tails determine "
                "whether V72 creates a new regression; the absolute result is not "
                "relabelled as a stock-wide grain measurement."
            ),
        }
        for branch in BRANCHES:
            grain_branch = "scan" if branch == "bluray_scan" else branch
            reference_result = reference_grain["scenes"]["T003_frame160"][
                grain_branch
            ]
            candidate_result = candidate_grain["scenes"]["T003_frame160"][
                grain_branch
            ]
            reference_worst = reference_result["worst"]
            candidate_worst = candidate_result["worst"]
            fields = (
                "dark_opponent_p9999",
                "median_opponent_p9999",
                "isolated_impulses_gt_0.06_per_million",
                "isolated_impulses_gt_0.08_per_million",
            )
            paired["branches"][branch] = {
                "reference_absolute_gate_pass": reference_result["pass"],
                "candidate_absolute_gate_pass": candidate_result["pass"],
                "metrics": {
                    field: {
                        "reference": reference_worst[field],
                        "candidate": candidate_worst[field],
                        "candidate_minus_reference": (
                            candidate_worst[field] - reference_worst[field]
                        ),
                    }
                    for field in fields
                },
            }
            gates[f"T003_{branch}_paired_dark_opponent_no_regression"] = bool(
                candidate_worst["dark_opponent_p9999"]
                <= reference_worst["dark_opponent_p9999"] + 0.001
            )
            gates[f"T003_{branch}_paired_median_opponent_no_regression"] = bool(
                candidate_worst["median_opponent_p9999"]
                <= reference_worst["median_opponent_p9999"] + 0.001
            )
            gates[f"T003_{branch}_paired_isolated_006_no_regression"] = bool(
                candidate_worst["isolated_impulses_gt_0.06_per_million"]
                <= reference_worst["isolated_impulses_gt_0.06_per_million"] + 1.0
            )
            gates[f"T003_{branch}_isolated_008_within_safe_tail"] = bool(
                candidate_worst["isolated_impulses_gt_0.08_per_million"] <= 1.0
            )
        report["paired_native_colour_grain"] = paired
    report["gates"] = gates
    report["all_gates_pass"] = bool(all(gates.values()))
    report["decision_boundary"] = {
        "what_this_can_support": (
            "identity is a stable evidence-minimal endpoint for the otherwise "
            "unidentified direct record-mix operator"
        ),
        "what_this_cannot_support": (
            "the true joint 5279 grain covariance or exact separation response; "
            "those still require controlled uniform and separation-wedge measurements"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_gates_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
