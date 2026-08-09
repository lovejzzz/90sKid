#!/usr/bin/env python3
"""Compare matched V34/V35 masters over time, chroma, tails and texture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np


RELEASE_GATES = {
    "absolute_temporal_mean_rgb_delta": 1.0e-4,
    "absolute_highpass_std_ratio_minus_one": 0.02,
    "absolute_highpass_correlation_delta": 0.02,
    "absolute_temporal_difference_std_ratio_minus_one": 0.02,
    "absolute_clip_fraction_delta": 1.0e-4,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decoder(path: Path, filter_graph: str, width: int, height: int):
    process = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-an",
            "-vf", filter_graph, "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    assert process.stdout is not None
    return process, width * height * 3 * 2


def read_frame(process, frame_bytes: int, shape: tuple[int, int, int]):
    payload = process.stdout.read(frame_bytes)
    if not payload:
        return None
    if len(payload) != frame_bytes:
        raise RuntimeError("truncated ffmpeg frame")
    return (
        np.frombuffer(payload, dtype="<u2").reshape(shape).astype(np.float32)
        / 65535.0
    )


def global_metrics(reference: Path, candidate: Path) -> dict:
    width, height = 1440, 1080
    graph = f"scale={width}:{height}:flags=area"
    ref, frame_bytes = decoder(reference, graph, width, height)
    can, _ = decoder(candidate, graph, width, height)
    rows = []
    while True:
        a = read_frame(ref, frame_bytes, (height, width, 3))
        b = read_frame(can, frame_bytes, (height, width, 3))
        if a is None or b is None:
            if a is not None or b is not None:
                raise RuntimeError("frame count mismatch")
            break
        la = np.einsum("...c,c->...", a, [0.2126, 0.7152, 0.0722])
        lb = np.einsum("...c,c->...", b, [0.2126, 0.7152, 0.0722])
        rows.append(
            {
                "mean_rgb_delta": (b.mean((0, 1)) - a.mean((0, 1))).tolist(),
                "luma_percentile_delta": (
                    np.percentile(lb, [0.1, 1, 50, 99, 99.9])
                    - np.percentile(la, [0.1, 1, 50, 99, 99.9])
                ).tolist(),
                "mean_absolute_rgb_delta": np.abs(b - a).mean((0, 1)).tolist(),
                "reference_low_clip_fraction_rgb": np.mean(
                    a <= (1.0 / 65535.0), axis=(0, 1)
                ).tolist(),
                "candidate_low_clip_fraction_rgb": np.mean(
                    b <= (1.0 / 65535.0), axis=(0, 1)
                ).tolist(),
                "reference_high_clip_fraction_rgb": np.mean(
                    a >= (65534.0 / 65535.0), axis=(0, 1)
                ).tolist(),
                "candidate_high_clip_fraction_rgb": np.mean(
                    b >= (65534.0 / 65535.0), axis=(0, 1)
                ).tolist(),
            }
        )
    if ref.wait() or can.wait():
        raise RuntimeError("ffmpeg global decode failed")
    mean_delta = np.array([row["mean_rgb_delta"] for row in rows])
    luma_delta = np.array([row["luma_percentile_delta"] for row in rows])
    low_delta = np.array(
        [
            np.array(row["candidate_low_clip_fraction_rgb"])
            - np.array(row["reference_low_clip_fraction_rgb"])
            for row in rows
        ]
    )
    high_delta = np.array(
        [
            np.array(row["candidate_high_clip_fraction_rgb"])
            - np.array(row["reference_high_clip_fraction_rgb"])
            for row in rows
        ]
    )
    return {
        "frames": len(rows),
        "temporal_mean_rgb_delta": mean_delta.mean(axis=0).tolist(),
        "temporal_std_rgb_delta": mean_delta.std(axis=0).tolist(),
        "maximum_absolute_frame_mean_rgb_delta": np.max(
            np.abs(mean_delta), axis=0
        ).tolist(),
        "temporal_mean_luma_p001_p01_p50_p99_p999_delta": luma_delta.mean(
            axis=0
        ).tolist(),
        "temporal_mean_low_clip_fraction_delta_rgb": low_delta.mean(axis=0).tolist(),
        "temporal_mean_high_clip_fraction_delta_rgb": high_delta.mean(axis=0).tolist(),
        "maximum_absolute_clip_fraction_delta": float(
            max(np.max(np.abs(low_delta)), np.max(np.abs(high_delta)))
        ),
        "per_frame": rows,
    }


def correlation_from_covariance(covariance: np.ndarray) -> np.ndarray:
    scale = np.sqrt(np.maximum(np.diag(covariance), 1e-30))
    return covariance / np.outer(scale, scale)


def crop_texture_metrics(
    reference: Path,
    candidate: Path,
    *,
    x: int,
    y: int,
    size: int,
) -> dict:
    graph = f"crop={size}:{size}:{x}:{y}"
    ref, frame_bytes = decoder(reference, graph, size, size)
    can, _ = decoder(candidate, graph, size, size)
    rows = []
    previous_a = previous_b = None
    while True:
        a = read_frame(ref, frame_bytes, (size, size, 3))
        b = read_frame(can, frame_bytes, (size, size, 3))
        if a is None or b is None:
            if a is not None or b is not None:
                raise RuntimeError("frame count mismatch")
            break
        high_a = a - cv2.GaussianBlur(a, (0, 0), 3, borderType=cv2.BORDER_REFLECT)
        high_b = b - cv2.GaussianBlur(b, (0, 0), 3, borderType=cv2.BORDER_REFLECT)
        covariance_a = np.cov(high_a.reshape(-1, 3), rowvar=False, bias=True)
        covariance_b = np.cov(high_b.reshape(-1, 3), rowvar=False, bias=True)
        row = {
            "highpass_std_ratio": (
                high_b.std((0, 1)) / high_a.std((0, 1))
            ).tolist(),
            "reference_highpass_correlation": correlation_from_covariance(
                covariance_a
            ).tolist(),
            "candidate_highpass_correlation": correlation_from_covariance(
                covariance_b
            ).tolist(),
        }
        if previous_a is not None:
            temporal_a = high_a - previous_a
            temporal_b = high_b - previous_b
            row["temporal_difference_std_ratio"] = (
                temporal_b.std((0, 1)) / temporal_a.std((0, 1))
            ).tolist()
        rows.append(row)
        previous_a, previous_b = high_a, high_b
    if ref.wait() or can.wait():
        raise RuntimeError("ffmpeg texture decode failed")
    std_ratios = np.asarray([row["highpass_std_ratio"] for row in rows])
    temporal_ratios = np.asarray(
        [row["temporal_difference_std_ratio"] for row in rows[1:]]
    )
    correlation_delta = np.asarray(
        [
            np.asarray(row["candidate_highpass_correlation"])
            - np.asarray(row["reference_highpass_correlation"])
            for row in rows
        ]
    )
    return {
        "crop": {"x": x, "y": y, "size": size},
        "frames": len(rows),
        "highpass_std_ratio_temporal_mean": std_ratios.mean(axis=0).tolist(),
        "highpass_std_ratio_temporal_std": std_ratios.std(axis=0).tolist(),
        "temporal_difference_std_ratio_mean": temporal_ratios.mean(axis=0).tolist(),
        "maximum_absolute_highpass_correlation_delta": float(
            np.max(np.abs(correlation_delta))
        ),
        "mean_highpass_correlation_delta": correlation_delta.mean(axis=0).tolist(),
        "per_frame": rows,
    }


def texture_metrics(reference: Path, candidate: Path) -> dict:
    crops = {
        "centre": (2624, 1904),
        "upper_left": (512, 512),
        "upper_right": (4736, 512),
        "lower_left": (512, 3296),
        "lower_right": (4736, 3296),
    }
    results = {
        name: crop_texture_metrics(
            reference, candidate, x=x, y=y, size=512
        )
        for name, (x, y) in crops.items()
    }
    all_std = np.array(
        [result["highpass_std_ratio_temporal_mean"] for result in results.values()]
    )
    all_temporal = np.array(
        [result["temporal_difference_std_ratio_mean"] for result in results.values()]
    )
    return {
        "crops": results,
        "maximum_absolute_highpass_std_ratio_minus_one": float(
            np.max(np.abs(all_std - 1.0))
        ),
        "maximum_absolute_temporal_difference_std_ratio_minus_one": float(
            np.max(np.abs(all_temporal - 1.0))
        ),
        "maximum_absolute_highpass_correlation_delta": max(
            result["maximum_absolute_highpass_correlation_delta"]
            for result in results.values()
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "reference": str(args.reference),
        "candidate": str(args.candidate),
        "provenance": {
            "reference_sha256": sha256(args.reference),
            "candidate_sha256": sha256(args.candidate),
            "comparison_script_sha256": sha256(Path(__file__)),
        },
        "release_gates": RELEASE_GATES,
        "global": global_metrics(args.reference, args.candidate),
        "texture": texture_metrics(args.reference, args.candidate),
    }
    result["gate_results"] = {
        "temporal_mean_rgb": bool(
            np.max(np.abs(result["global"]["temporal_mean_rgb_delta"]))
            <= RELEASE_GATES["absolute_temporal_mean_rgb_delta"]
        ),
        "clip_fraction": bool(
            result["global"]["maximum_absolute_clip_fraction_delta"]
            <= RELEASE_GATES["absolute_clip_fraction_delta"]
        ),
        "highpass_energy": bool(
            result["texture"]["maximum_absolute_highpass_std_ratio_minus_one"]
            <= RELEASE_GATES["absolute_highpass_std_ratio_minus_one"]
        ),
        "highpass_chroma_correlation": bool(
            result["texture"]["maximum_absolute_highpass_correlation_delta"]
            <= RELEASE_GATES["absolute_highpass_correlation_delta"]
        ),
        "temporal_difference_energy": bool(
            result["texture"][
                "maximum_absolute_temporal_difference_std_ratio_minus_one"
            ]
            <= RELEASE_GATES[
                "absolute_temporal_difference_std_ratio_minus_one"
            ]
        ),
    }
    result["all_release_gates_pass"] = all(result["gate_results"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "global": {
                    key: value
                    for key, value in result["global"].items()
                    if key != "per_frame"
                },
                "texture_summary": {
                    key: value
                    for key, value in result["texture"].items()
                    if key != "crops"
                },
                "gate_results": result["gate_results"],
                "all_release_gates_pass": result["all_release_gates_pass"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
