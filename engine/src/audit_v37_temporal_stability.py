#!/usr/bin/env python3
"""Compare framewise sampling stability on source-matched native masters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from diagnose_v35_grain_perception import ANCHORS, decode_crop, probe


LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def framewise_metrics(frames: np.ndarray) -> dict[str, object]:
    rows = []
    for frame in frames:
        luma = np.einsum("...c,c->...", frame, LUMA)
        highpass = luma - cv2.GaussianBlur(
            luma, (0, 0), 3.0, borderType=cv2.BORDER_REFLECT
        )
        gradient_x = cv2.Sobel(highpass, cv2.CV_32F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(highpass, cv2.CV_32F, 0, 1, ksize=3)
        rows.append(
            [
                float(np.sqrt(np.mean(highpass * highpass))),
                float(
                    np.mean(gradient_x * gradient_x)
                    / max(float(np.mean(gradient_y * gradient_y)), 1e-30)
                ),
            ]
        )
    values = np.asarray(rows, dtype=np.float64)
    return {
        "frames": int(values.shape[0]),
        "highpass_rms_mean": float(np.mean(values[:, 0])),
        "highpass_rms_coefficient_of_variation": float(
            np.std(values[:, 0]) / max(float(np.mean(values[:, 0])), 1e-30)
        ),
        "xy_anisotropy_mean": float(np.mean(values[:, 1])),
        "xy_anisotropy_standard_deviation": float(np.std(values[:, 1])),
        "per_frame": [
            {"highpass_rms": float(row[0]), "xy_anisotropy": float(row[1])}
            for row in values
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    width_a, height_a, frames_a = probe(args.reference)
    width_b, height_b, frames_b = probe(args.candidate)
    if (width_a, height_a, frames_a) != (width_b, height_b, frames_b):
        raise ValueError("reference and candidate dimensions/frame counts differ")
    scale = min(width_a / 5760.0, height_a / 4320.0)
    crop_size = max(128, int(round(512 * scale)))
    crop_size -= crop_size % 2
    crops = {}
    for name, (cx, cy) in ANCHORS.items():
        x = min(max(int(round(cx * width_a - crop_size / 2)), 0), width_a - crop_size)
        y = min(max(int(round(cy * height_a - crop_size / 2)), 0), height_a - crop_size)
        reference = framewise_metrics(decode_crop(args.reference, x, y, crop_size))
        candidate = framewise_metrics(decode_crop(args.candidate, x, y, crop_size))
        crops[name] = {
            "crop": {"x": x, "y": y, "size": crop_size},
            "reference": reference,
            "candidate": candidate,
            "candidate_over_reference": {
                "highpass_rms_mean": (
                    candidate["highpass_rms_mean"] / reference["highpass_rms_mean"]
                ),
                "highpass_rms_coefficient_of_variation": (
                    candidate["highpass_rms_coefficient_of_variation"]
                    / max(reference["highpass_rms_coefficient_of_variation"], 1e-30)
                ),
                "xy_anisotropy_standard_deviation": (
                    candidate["xy_anisotropy_standard_deviation"]
                    / max(reference["xy_anisotropy_standard_deviation"], 1e-30)
                ),
            },
        }
        print(f"measured {name}", flush=True)

    ratios = [entry["candidate_over_reference"] for entry in crops.values()]
    summary = {
        key: {
            "median": float(np.median([row[key] for row in ratios])),
            "minimum": float(np.min([row[key] for row in ratios])),
            "maximum": float(np.max([row[key] for row in ratios])),
        }
        for key in ratios[0]
    }
    result = {
        "reference": str(args.reference),
        "candidate": str(args.candidate),
        "dimensions": [width_a, height_a],
        "frames": frames_a,
        "crop_size": crop_size,
        "summary": summary,
        "crops": crops,
        "boundary": (
            "Exact source frames are required. Scene motion remains in both branches, "
            "so ratios identify candidate-induced stability rather than absolute film limits."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
