#!/usr/bin/env python3
"""Compare scale-integrated review delivery codecs without changing film pixels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np

import emulsion_experiment as e
import v72_profile
from audit_v63_neutral_trajectory import difference_metrics
from audit_v69_cineon_view_policy import structure_summary
from audit_v75_scale_integrated_delivery import (
    BRANCHES,
    INTEGRATED_REVIEW,
    MASTER,
    decode_code,
    exact_integer_area,
    probe,
)


def codec_probe(path: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            (
                "stream=codec_name,profile,width,height,pix_fmt,color_range,"
                "color_space,color_transfer,color_primaries,bits_per_raw_sample"
            ),
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    return json.loads(payload)["streams"][0]


def common_input(width: int, height: int, fps: str) -> list[str]:
    return [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb48le",
        "-s",
        f"{width}x{height}",
        "-r",
        fps,
        "-i",
        "pipe:0",
        "-frames:v",
        "1",
        "-an",
    ]


def prores_tail(path: Path) -> list[str]:
    return [
        "-color_primaries",
        "bt709",
        "-color_trc",
        "iec61966-2-1",
        "-colorspace",
        "bt709",
        "-movflags",
        "write_colr",
        str(path),
    ]


def commands(directory: Path, width: int, height: int, fps: str) -> dict[str, list[str]]:
    base = common_input(width, height, fps)
    ks = directory / "prores_ks_xq.mov"
    ks_max = directory / "prores_ks_xq_8192.mov"
    vt = directory / "prores_videotoolbox_xq.mov"
    ffv1 = directory / "ffv1_lossless.mkv"
    return {
        "prores_ks_xq": base
        + [
            "-c:v",
            "prores_ks",
            "-profile:v",
            "5",
            "-vendor",
            "apl0",
            "-pix_fmt",
            "yuv444p12le",
            "-bsf:v",
            (
                "prores_metadata=color_primaries=bt709:"
                "color_trc=unknown:colorspace=bt709"
            ),
        ]
        + prores_tail(ks),
        "prores_ks_xq_8192": base
        + [
            "-c:v",
            "prores_ks",
            "-profile:v",
            "5",
            "-bits_per_mb",
            "8192",
            "-vendor",
            "apl0",
            "-pix_fmt",
            "yuv444p12le",
            "-bsf:v",
            (
                "prores_metadata=color_primaries=bt709:"
                "color_trc=unknown:colorspace=bt709"
            ),
        ]
        + prores_tail(ks_max),
        "prores_videotoolbox_xq": base
        + [
            "-c:v",
            "prores_videotoolbox",
            "-profile:v",
            "5",
            "-allow_sw",
            "1",
            "-pix_fmt",
            "p416le",
        ]
        + prores_tail(vt),
        "ffv1_lossless": base
        + [
            "-c:v",
            "ffv1",
            "-level",
            "3",
            "-pix_fmt",
            "gbrp16le",
            str(ffv1),
        ],
    }


def output_path(command: list[str]) -> Path:
    return Path(command[-1])


def compare(reference_code: np.ndarray, candidate_code: np.ndarray) -> dict[str, object]:
    reference_light = e.srgb_decode(reference_code)
    candidate_light = e.srgb_decode(candidate_code)
    reference_structure = structure_summary(reference_light)
    candidate_structure = structure_summary(candidate_light)
    code_delta = np.abs(reference_code - candidate_code)
    return {
        "code_mae": float(np.mean(code_delta, dtype=np.float64)),
        "code_p99_absolute": float(np.percentile(code_delta, 99.0)),
        "code_maximum_absolute": float(np.max(code_delta)),
        "linear_light_difference": difference_metrics(
            reference_light, candidate_light
        ),
        "highpass_luma_retention": (
            candidate_structure["highpass_luma_rms"]
            / max(reference_structure["highpass_luma_rms"], 1e-30)
        ),
        "highpass_opponent_retention": (
            candidate_structure["highpass_opponent_rms"]
            / max(reference_structure["highpass_opponent_rms"], 1e-30)
        ),
    }


def audit_branch(root: Path, branch: str, frame: int) -> dict[str, object]:
    directory = root / branch
    master_path = directory / MASTER
    review_path = directory / INTEGRATED_REVIEW
    master_metadata = probe(master_path)
    review_metadata = probe(review_path)
    master_code = decode_code(master_path, frame)
    master_light = e.bt1886_reference_decode(master_code)
    factor = master_light.shape[1] // int(review_metadata["width"])
    exact_light = exact_integer_area(master_light, factor)
    reference_code = e.srgb_encode(exact_light).astype(np.float32)
    payload = (
        np.rint(np.clip(reference_code, 0.0, 1.0) * 65535.0)
        .astype("<u2")
        .tobytes()
    )
    quantized_reference = (
        np.frombuffer(payload, dtype="<u2")
        .reshape(reference_code.shape)
        .astype(np.float32)
        / 65535.0
    )

    results: dict[str, object] = {
        "existing_scale_integrated_review": {
            "file": str(review_path),
            "metadata": codec_probe(review_path),
            "bytes": review_path.stat().st_size,
            "comparison": compare(quantized_reference, decode_code(review_path, frame)),
        }
    }
    with tempfile.TemporaryDirectory(prefix=f"v76-{branch}-") as temporary:
        temporary_path = Path(temporary)
        for name, command in commands(
            temporary_path,
            int(review_metadata["width"]),
            int(review_metadata["height"]),
            str(master_metadata["r_frame_rate"]),
        ).items():
            path = output_path(command)
            try:
                completed = subprocess.run(
                    command,
                    input=payload,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                if completed.returncode:
                    results[name] = {
                        "available": False,
                        "returncode": completed.returncode,
                        "stderr": completed.stderr.decode("utf-8", "replace"),
                    }
                    continue
                if path.suffix == ".mov":
                    e.finalize_prores_srgb_metadata(path)
                results[name] = {
                    "available": True,
                    "metadata": codec_probe(path),
                    "bytes": path.stat().st_size,
                    "comparison": compare(quantized_reference, decode_code(path, 0)),
                }
            finally:
                path.unlink(missing_ok=True)
    return {
        "source_master": str(master_path),
        "frame": frame,
        "dimensions": [
            int(review_metadata["width"]),
            int(review_metadata["height"]),
        ],
        "reference": "exact 3x3 linear-light integration, sRGB, RGB16 quantized",
        "encodings": results,
    }


def measure(root: Path, frame: int) -> dict[str, object]:
    v72_profile.apply(e)
    return {
        "audit": "V76 scale-integrated review codec ownership",
        "profile": v72_profile.PROFILE["name"],
        "image_change": "none",
        "root": str(root),
        "branches": {
            branch: audit_branch(root, branch, frame) for branch in BRANCHES
        },
        "decision_rule": (
            "A codec may improve the declared review only if decoded colour, "
            "luma structure and opponent structure are all no worse than the "
            "current encoder. Codec substitution must not alter the native "
            "master or any film-formation parameter."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--frame", type=int, default=0)
    args = parser.parse_args()
    report = measure(args.root, args.frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
