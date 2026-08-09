#!/usr/bin/env python3
"""Compare an aligned FCP Standard ProRes RAW reference with pipeline stages."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


def decode_frame(path: Path, frame: int, width: int) -> np.ndarray:
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    source_width = int(stream["width"])
    source_height = int(stream["height"])
    height = round(source_height * width / source_width)
    payload = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", f"select=eq(n\\,{frame}),scale={width}:{height}:flags=lanczos",
            "-vsync", "0", "-frames:v", "1", "-pix_fmt", "rgb48le",
            "-f", "rawvideo", "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    expected = width * height * 3 * 2
    if len(payload) != expected:
        raise RuntimeError(f"decoded {len(payload)} bytes; expected {expected}")
    return (
        np.frombuffer(payload, dtype="<u2")
        .reshape(height, width, 3)
        .astype(np.float32)
        / 65535.0
    )


def bt709_decode(signal: np.ndarray) -> np.ndarray:
    signal = np.clip(signal, 0.0, 1.0)
    return np.where(
        signal < 0.081,
        signal / 4.5,
        np.power((signal + 0.099) / 1.099, 1.0 / 0.45),
    ).astype(np.float32)


def statistics(image: np.ndarray) -> dict[str, object]:
    linear = bt709_decode(image)
    luma = np.einsum("...c,c->...", linear, [0.2126, 0.7152, 0.0722])
    encoded_luma = np.einsum("...c,c->...", image, [0.2126, 0.7152, 0.0722])
    chroma = np.max(image, axis=-1) - np.min(image, axis=-1)
    neutral = (encoded_luma > 0.06) & (encoded_luma < 0.88) & (chroma < 0.035)
    neutral_rgb = image[neutral]
    neutral_sum = np.maximum(neutral_rgb.sum(axis=-1, keepdims=True), 1e-8)
    neutral_chromaticity = np.mean(neutral_rgb / neutral_sum, axis=0)
    return {
        "signal_channel_mean": image.mean(axis=(0, 1)).tolist(),
        "signal_channel_q01_q50_q99": np.quantile(
            image, [0.01, 0.50, 0.99], axis=(0, 1)
        ).tolist(),
        "linear_luma_q001_q01_q50_q99_q999": np.quantile(
            luma, [0.001, 0.01, 0.50, 0.99, 0.999]
        ).tolist(),
        "signal_clip_fraction_black": float(np.mean(encoded_luma <= 1.0 / 1023.0)),
        "signal_clip_fraction_white": float(np.mean(encoded_luma >= 1022.0 / 1023.0)),
        "neutral_sample_fraction": float(np.mean(neutral)),
        "neutral_chromaticity_rgb": neutral_chromaticity.tolist(),
        "neutral_green_excess": float(
            neutral_chromaticity[1]
            - 0.5 * (neutral_chromaticity[0] + neutral_chromaticity[2])
        ),
    }


def structure_correlation(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref = cv2.Laplacian(cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY), cv2.CV_32F)
    test = cv2.Laplacian(cv2.cvtColor(candidate, cv2.COLOR_RGB2GRAY), cv2.CV_32F)
    return float(np.corrcoef(ref.ravel(), test.ravel())[0, 1])


def phase_shift(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    ref = cv2.Laplacian(cv2.cvtColor(reference, cv2.COLOR_RGB2GRAY), cv2.CV_32F)
    test = cv2.Laplacian(cv2.cvtColor(candidate, cv2.COLOR_RGB2GRAY), cv2.CV_32F)
    shift, response = cv2.phaseCorrelate(ref, test)
    return {
        "x_pixels_at_measurement_width": float(shift[0]),
        "y_pixels_at_measurement_width": float(shift[1]),
        "response": float(response),
    }


def chromaticity_on_mask(image: np.ndarray, mask: np.ndarray) -> list[float]:
    selected = image[mask]
    chromaticity = selected / np.maximum(selected.sum(axis=-1, keepdims=True), 1e-8)
    return np.mean(chromaticity, axis=0).tolist()


def neutral_mask(image: np.ndarray) -> np.ndarray:
    luma = np.einsum("...c,c->...", image, [0.2126, 0.7152, 0.0722])
    chroma = np.max(image, axis=-1) - np.min(image, axis=-1)
    return (luma > 0.06) & (luma < 0.88) & (chroma < 0.035)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fcp", type=Path, required=True)
    parser.add_argument("--camera", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--scan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fcp-frame", type=int, default=0)
    parser.add_argument("--pipeline-frame", type=int, default=12)
    parser.add_argument("--width", type=int, default=1440)
    args = parser.parse_args()

    frames = {
        "fcp_standard": decode_frame(args.fcp, args.fcp_frame, args.width),
        "camera_v709": decode_frame(args.camera, args.pipeline_frame, args.width),
        "projection_2383": decode_frame(args.projection, args.pipeline_frame, args.width),
        "bluray_scan": decode_frame(args.scan, args.pipeline_frame, args.width),
    }
    reference = frames["fcp_standard"]
    common_neutral = neutral_mask(reference)
    report = {
        "alignment": {
            "fcp_source_frame": 144,
            "pipeline_source_frame": 132 + args.pipeline_frame,
            "dimensions_for_measurement": list(reference.shape[1::-1]),
        },
        "common_fcp_neutral_mask_fraction": float(np.mean(common_neutral)),
        "stages": {},
    }
    for name, image in frames.items():
        metrics = statistics(image)
        metrics["laplacian_structure_correlation_to_fcp"] = structure_correlation(
            reference, image
        )
        metrics["phase_shift_to_fcp"] = phase_shift(reference, image)
        metrics["chromaticity_on_common_fcp_neutral_mask"] = chromaticity_on_mask(
            image, common_neutral
        )
        intersection = common_neutral & neutral_mask(image)
        metrics["pairwise_neutral_intersection_fraction"] = float(
            np.mean(intersection)
        )
        metrics["fcp_chromaticity_on_pairwise_neutral_intersection"] = (
            chromaticity_on_mask(reference, intersection)
        )
        metrics["stage_chromaticity_on_pairwise_neutral_intersection"] = (
            chromaticity_on_mask(image, intersection)
        )
        report["stages"][name] = metrics
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
