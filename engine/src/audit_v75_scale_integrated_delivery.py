#!/usr/bin/env python3
"""Audit V72 native-companion versus scale-integrated review delivery.

The native master is image authority, but a 5.7K stochastic density field is
not a scale-independent viewing raster.  This audit verifies the exact 3x3
linear-light integration path, quantifies sharp-resize alternatives and states
which QuickTime file answers which viewing question.  It changes no pixels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np

import emulsion_experiment as e
import v72_profile
from audit_v63_neutral_trajectory import difference_metrics
from audit_v69_cineon_view_policy import structure_summary


BRANCHES = ("projection", "bluray_scan")
MASTER = "05_emulsion_master_prores4444.mov"
NATIVE_COMPANION = "06_quicktime_preview_srgb_prores4444.mov"
INTEGRATED_REVIEW = "07_scale_integrated_review_srgb_prores4444.mov"


def probe(path: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            (
                "stream=width,height,pix_fmt,color_primaries,color_transfer,"
                "color_space,r_frame_rate,nb_frames"
            ),
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    return json.loads(payload)["streams"][0]


def decode_code(path: Path, frame: int) -> np.ndarray:
    metadata = probe(path)
    width, height = int(metadata["width"]), int(metadata["height"])
    payload = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-vf",
            (
                f"select=eq(n\\,{frame}),setparams=color_primaries=bt709:"
                "color_trc=bt709:colorspace=bt709"
            ),
            "-vsync",
            "0",
            "-frames:v",
            "1",
            "-pix_fmt",
            "rgb48le",
            "-f",
            "rawvideo",
            "-",
        ]
    )
    expected = width * height * 3 * 2
    if len(payload) != expected:
        raise RuntimeError(f"decoded {len(payload)} bytes; expected {expected}")
    return (
        np.frombuffer(payload, dtype="<u2")
        .reshape(height, width, 3)
        .astype(np.float32)
        / 65535.0
    )


def exact_integer_area(image: np.ndarray, factor: int) -> np.ndarray:
    height, width = image.shape[:2]
    if height % factor or width % factor:
        raise ValueError("source dimensions must be divisible by integration factor")
    return image.reshape(
        height // factor, factor, width // factor, factor, image.shape[2]
    ).mean(axis=(1, 3), dtype=np.float64).astype(np.float32)


def resampling_comparison(reference: np.ndarray, candidate: np.ndarray) -> dict[str, object]:
    reference_structure = structure_summary(reference)
    candidate_structure = structure_summary(candidate)
    return {
        "difference": difference_metrics(reference, candidate),
        "reference_structure": reference_structure,
        "candidate_structure": candidate_structure,
        "candidate_over_reference_highpass_luma_rms": (
            candidate_structure["highpass_luma_rms"]
            / max(reference_structure["highpass_luma_rms"], 1e-30)
        ),
        "candidate_over_reference_highpass_opponent_rms": (
            candidate_structure["highpass_opponent_rms"]
            / max(reference_structure["highpass_opponent_rms"], 1e-30)
        ),
    }


def branch_audit(root: Path, branch: str, frame: int) -> dict[str, object]:
    directory = root / branch
    master_path = directory / MASTER
    companion_path = directory / NATIVE_COMPANION
    review_path = directory / INTEGRATED_REVIEW
    master_code = decode_code(master_path, frame)
    companion_code = decode_code(companion_path, frame)
    review_code = decode_code(review_path, frame)

    master_light = e.bt1886_reference_decode(master_code)
    companion_light = e.srgb_decode(companion_code)
    review_light = e.srgb_decode(review_code)
    target = (int(probe(review_path)["width"]), int(probe(review_path)["height"]))
    factor = master_light.shape[1] // target[0]
    exact = exact_integer_area(master_light, factor)
    opencv_area = cv2.resize(master_light, target, interpolation=cv2.INTER_AREA)
    native_companion_area = cv2.resize(
        companion_light, target, interpolation=cv2.INTER_AREA
    )
    linear_lanczos = cv2.resize(
        master_light, target, interpolation=cv2.INTER_LANCZOS4
    )
    code_lanczos = e.srgb_decode(
        np.clip(
            cv2.resize(companion_code, target, interpolation=cv2.INTER_LANCZOS4),
            0.0,
            1.0,
        )
    )

    area_exact_delta = np.abs(opencv_area - exact)
    return {
        "files": {
            "master": str(master_path),
            "native_srgb_companion": str(companion_path),
            "scale_integrated_review": str(review_path),
        },
        "metadata": {
            "master": probe(master_path),
            "native_srgb_companion": probe(companion_path),
            "scale_integrated_review": probe(review_path),
        },
        "integration_factor": factor,
        "opencv_area_vs_exact_3x3": {
            "maximum_absolute_linear_light_difference": float(
                np.max(area_exact_delta)
            ),
            "mean_absolute_linear_light_difference": float(
                np.mean(area_exact_delta)
            ),
            "exact_within_float32_rounding": bool(np.max(area_exact_delta) <= 2e-7),
        },
        "decoded_review_vs_exact_master_integration": resampling_comparison(
            exact, review_light
        ),
        "integrated_native_companion_vs_exact_master_integration": (
            resampling_comparison(exact, native_companion_area)
        ),
        "linear_light_lanczos_vs_exact_area": resampling_comparison(
            exact, linear_lanczos
        ),
        "srgb_code_lanczos_vs_exact_linear_area": resampling_comparison(
            exact, code_lanczos
        ),
    }


def uniform_grain_resampling(log_exposure: float = -3.0) -> dict[str, object]:
    v72_profile.apply(e)
    e.BINOMIAL_SAMPLER_MODE = "striped_v25"
    e.BINOMIAL_PARALLEL_WORKERS = 4
    height, width = 192, 5760
    records = np.full(
        (height, width, 3), 10.0 ** (log_exposure + 1.0), dtype=np.float32
    )
    mean = e.develop_5279_record_density(records)
    formed = e.form_5279_multilayer_record_density(
        records,
        7500,
        1.0,
        1,
        precomputed_mean_density=mean,
    )
    residual = formed - mean
    target = (width // 3, height // 3)
    exact = exact_integer_area(residual, 3)
    lanczos = cv2.resize(residual, target, interpolation=cv2.INTER_LANCZOS4)
    area_rms = np.sqrt(np.mean(exact * exact, axis=(0, 1), dtype=np.float64))
    lanczos_rms = np.sqrt(
        np.mean(lanczos * lanczos, axis=(0, 1), dtype=np.float64)
    )
    return {
        "log_exposure": log_exposure,
        "source_dimensions": [width, height],
        "target_dimensions": list(target),
        "grain_only_area_rms_rgb": area_rms.tolist(),
        "grain_only_lanczos_rms_rgb": lanczos_rms.tolist(),
        "lanczos_over_area_rms_rgb": (
            lanczos_rms / np.maximum(area_rms, 1e-30)
        ).tolist(),
        "interpretation": (
            "Lanczos is a deliberately sharp diagnostic, not a claim about "
            "QuickTime's private compositor. It demonstrates how a resize that "
            "does not integrate source-pixel area can retain or fold native "
            "grain energy into a coarser review raster."
        ),
    }


def measure(root: Path, frame: int, include_uniform: bool) -> dict[str, object]:
    v72_profile.apply(e)
    branches = {branch: branch_audit(root, branch, frame) for branch in BRANCHES}
    all_exact = all(
        branch["opencv_area_vs_exact_3x3"]["exact_within_float32_rounding"]
        for branch in branches.values()
    )
    report: dict[str, object] = {
        "audit": "V75 scale-integrated delivery ownership",
        "profile": v72_profile.PROFILE["name"],
        "image_change": "none",
        "root": str(root),
        "frame": frame,
        "branches": branches,
        "gates": {
            "opencv_area_is_exact_3x3_linear_integration": all_exact,
            "master_5760_native_companion_5760_review_1920": all(
                int(branch["metadata"]["master"]["width"]) == 5760
                and int(branch["metadata"]["native_srgb_companion"]["width"])
                == 5760
                and int(branch["metadata"]["scale_integrated_review"]["width"])
                == 1920
                for branch in branches.values()
            ),
        },
        "file_roles": {
            MASTER: (
                "native 5760x4320 12-bit BT.1886 picture authority; inspect at "
                "1:1 for native samples or use a declared viewing integration"
            ),
            NATIVE_COMPANION: (
                "native-resolution sRGB transfer of the encoded master; it does "
                "not own a 1920-window resampling policy"
            ),
            INTEGRATED_REVIEW: (
                "declared 1920x1440 linear-light 3x3 pixel-area integration; "
                "preferred file for judging 2K-scale grain geometry in "
                "QuickTime, while its final ProRes encode is not a lossless "
                "NPS authority"
            ),
        },
        "decoded_structure_retention": {
            "scale_integrated_review_luma": [
                branches[branch]["decoded_review_vs_exact_master_integration"]
                ["candidate_over_reference_highpass_luma_rms"]
                for branch in BRANCHES
            ],
            "scale_integrated_review_opponent": [
                branches[branch]["decoded_review_vs_exact_master_integration"]
                ["candidate_over_reference_highpass_opponent_rms"]
                for branch in BRANCHES
            ],
            "area_integrated_native_companion_luma": [
                branches[branch]
                ["integrated_native_companion_vs_exact_master_integration"]
                ["candidate_over_reference_highpass_luma_rms"]
                for branch in BRANCHES
            ],
            "area_integrated_native_companion_opponent": [
                branches[branch]
                ["integrated_native_companion_vs_exact_master_integration"]
                ["candidate_over_reference_highpass_opponent_rms"]
                for branch in BRANCHES
            ],
        },
        "decision": (
            "Keep one native master and the separate scale-declared review. "
            "Use the review to control viewing scale, but do not treat either "
            "its lossy ProRes high-pass amplitude or an unknown player resize "
            "of the 5760 companion as an NPS measurement. Do not tune the "
            "film model to compensate for either delivery effect."
        ),
    }
    if include_uniform:
        report["uniform_grain_only_resampling"] = uniform_grain_resampling()
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--skip-uniform", action="store_true")
    args = parser.parse_args()
    result = measure(args.root, args.frame, not args.skip_uniform)
    payload = json.dumps(result, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
