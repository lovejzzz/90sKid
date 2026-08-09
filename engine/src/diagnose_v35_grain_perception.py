#!/usr/bin/env python3
"""Measure perceptual grain motion that energy-only V34/V35 gates can miss."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import cv2
import numpy as np


ANCHORS = {
    "centre": (0.50, 0.50),
    "upper_left": (0.133333, 0.177778),
    "upper_right": (0.866667, 0.177778),
    "lower_left": (0.133333, 0.822222),
    "lower_right": (0.866667, 0.822222),
}
LUMA_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], np.float32)
NPS_EDGES = np.array([0.0, 0.03125, 0.0625, 0.125, 0.25, 0.5, 0.71])


def probe(path: Path) -> tuple[int, int, int]:
    stream = json.loads(
        subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,nb_frames", "-of", "json",
                str(path),
            ],
            text=True,
        )
    )["streams"][0]
    return int(stream["width"]), int(stream["height"]), int(stream["nb_frames"])


def decode_crop(path: Path, x: int, y: int, size: int) -> np.ndarray:
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-an", "-vf",
            f"crop={size}:{size}:{x}:{y}", "-pix_fmt", "rgb48le", "-f",
            "rawvideo", "-",
        ]
    )
    frame_bytes = size * size * 3 * 2
    if len(payload) % frame_bytes:
        raise RuntimeError(f"{path}: truncated crop decode")
    return (
        np.frombuffer(payload, dtype="<u2")
        .reshape(-1, size, size, 3)
        .astype(np.float32)
        / 65535.0
    )


def excess_kurtosis(values: np.ndarray) -> float:
    values = values.astype(np.float64, copy=False)
    centered = values - values.mean()
    variance = np.mean(centered * centered)
    return float(np.mean(centered**4) / max(variance * variance, 1e-30) - 3.0)


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float64, copy=False)
    b = b.astype(np.float64, copy=False)
    a = a - a.mean()
    b = b - b.mean()
    return float(np.mean(a * b) / max(a.std() * b.std(), 1e-30))


def radial_nps(signal: np.ndarray) -> list[float]:
    frames, height, width = signal.shape
    window = np.outer(np.hanning(height), np.hanning(width)).astype(np.float32)
    fy = np.fft.fftfreq(height)[:, None]
    fx = np.fft.rfftfreq(width)[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    power = np.zeros((height, width // 2 + 1), np.float64)
    for frame in signal:
        transformed = np.fft.rfft2((frame - frame.mean()) * window)
        power += np.abs(transformed) ** 2
    band_power = []
    for low, high in zip(NPS_EDGES[:-1], NPS_EDGES[1:]):
        mask = (radius >= low) & (radius < high)
        band_power.append(float(power[mask].sum()))
    total = max(sum(band_power), 1e-30)
    return [value / total for value in band_power]


def component_areas(signal: np.ndarray, threshold: float) -> np.ndarray:
    areas: list[int] = []
    for frame in signal:
        mask = (np.abs(frame) > threshold).astype(np.uint8)
        count, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
        if count > 1:
            areas.extend(stats[1:, cv2.CC_STAT_AREA].tolist())
    return np.asarray(areas or [0], np.float64)


def metrics(frames: np.ndarray) -> dict[str, object]:
    hp_rgb = np.empty_like(frames)
    for t, frame in enumerate(frames):
        hp_rgb[t] = frame - cv2.GaussianBlur(
            frame, (0, 0), 3.0, borderType=cv2.BORDER_REFLECT
        )
    hp_luma = np.einsum("...c,c->...", hp_rgb, LUMA_WEIGHTS)
    luma = np.einsum("...c,c->...", frames, LUMA_WEIGHTS)
    base = luma - hp_luma
    diff_luma = np.diff(hp_luma, axis=0)
    diff_rgb = np.diff(hp_rgb, axis=0)
    diff_opponent = diff_rgb - diff_luma[..., None]

    diff_rms = float(np.sqrt(np.mean(diff_luma * diff_luma)))
    hp_rms = float(np.sqrt(np.mean(hp_luma * hp_luma)))
    gradient_p90 = float(
        np.percentile(
            np.concatenate(
                [
                    np.hypot(
                        cv2.Sobel(frame, cv2.CV_32F, 1, 0, ksize=3),
                        cv2.Sobel(frame, cv2.CV_32F, 0, 1, ksize=3),
                    ).ravel()
                    for frame in base
                ]
            ),
            90,
        )
    )
    threshold = 4.0 * diff_rms
    areas = component_areas(diff_luma, threshold)
    temporal_std = np.std(hp_luma, axis=0)
    abs_diff = np.abs(diff_luma)

    return {
        "frames": int(frames.shape[0]),
        "highpass_luma_rms": hp_rms,
        "highpass_luma_excess_kurtosis": excess_kurtosis(hp_luma),
        "temporal_difference_rms": diff_rms,
        "temporal_difference_abs_p95_p99_p999_p9999": np.percentile(
            abs_diff, [95, 99, 99.9, 99.99]
        ).tolist(),
        "temporal_difference_excess_kurtosis": excess_kurtosis(diff_luma),
        "temporal_lag1_correlation": correlation(hp_luma[:-1], hp_luma[1:]),
        "spatial_x_lag1_correlation": correlation(hp_luma[:, :, :-1], hp_luma[:, :, 1:]),
        "spatial_y_lag1_correlation": correlation(hp_luma[:, :-1, :], hp_luma[:, 1:, :]),
        "temporal_pixel_std_p50_p90_p99_p999": np.percentile(
            temporal_std, [50, 90, 99, 99.9]
        ).tolist(),
        "burst_fraction_over_3rms": float(np.mean(abs_diff > 3.0 * diff_rms)),
        "burst_fraction_over_4rms": float(np.mean(abs_diff > threshold)),
        "burst_component_area_p50_p90_p99_max": [
            float(np.percentile(areas, 50)),
            float(np.percentile(areas, 90)),
            float(np.percentile(areas, 99)),
            float(np.max(areas)),
        ],
        "opponent_to_luma_temporal_rms": float(
            np.sqrt(np.mean(diff_opponent * diff_opponent)) / max(diff_rms, 1e-30)
        ),
        "grain_to_base_edge_p90": hp_rms / max(gradient_p90, 1e-30),
        "normalized_nps_bands": radial_nps(hp_luma),
    }


def numeric_ratios(reference: dict, candidate: dict) -> dict[str, object]:
    scalar_keys = [
        "highpass_luma_rms",
        "temporal_difference_rms",
        "burst_fraction_over_3rms",
        "burst_fraction_over_4rms",
        "opponent_to_luma_temporal_rms",
        "grain_to_base_edge_p90",
    ]
    result: dict[str, object] = {
        key: float(candidate[key]) / max(float(reference[key]), 1e-30)
        for key in scalar_keys
    }
    for key in (
        "temporal_difference_abs_p95_p99_p999_p9999",
        "temporal_pixel_std_p50_p90_p99_p999",
        "normalized_nps_bands",
    ):
        result[key] = (
            np.asarray(candidate[key]) / np.maximum(np.asarray(reference[key]), 1e-30)
        ).tolist()
    result["temporal_lag1_correlation_delta"] = float(
        candidate["temporal_lag1_correlation"]
        - reference["temporal_lag1_correlation"]
    )
    result["spatial_lag1_correlation_delta_xy"] = [
        float(candidate["spatial_x_lag1_correlation"] - reference["spatial_x_lag1_correlation"]),
        float(candidate["spatial_y_lag1_correlation"] - reference["spatial_y_lag1_correlation"]),
    ]
    result["temporal_difference_kurtosis_delta"] = float(
        candidate["temporal_difference_excess_kurtosis"]
        - reference["temporal_difference_excess_kurtosis"]
    )
    return result


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
    crops: dict[str, object] = {}
    for name, (cx, cy) in ANCHORS.items():
        x = int(round(cx * width_a - crop_size / 2))
        y = int(round(cy * height_a - crop_size / 2))
        x = min(max(x, 0), width_a - crop_size)
        y = min(max(y, 0), height_a - crop_size)
        reference = metrics(decode_crop(args.reference, x, y, crop_size))
        candidate = metrics(decode_crop(args.candidate, x, y, crop_size))
        crops[name] = {
            "crop": {"x": x, "y": y, "size": crop_size},
            "reference": reference,
            "candidate": candidate,
            "candidate_over_reference": numeric_ratios(reference, candidate),
        }
        print(f"measured {name}", flush=True)

    ratio_rows = [item["candidate_over_reference"] for item in crops.values()]
    summary = {}
    for key in (
        "highpass_luma_rms",
        "temporal_difference_rms",
        "burst_fraction_over_3rms",
        "burst_fraction_over_4rms",
        "opponent_to_luma_temporal_rms",
        "grain_to_base_edge_p90",
        "temporal_lag1_correlation_delta",
        "temporal_difference_kurtosis_delta",
    ):
        values = np.asarray([row[key] for row in ratio_rows], np.float64)
        summary[key] = {
            "median": float(np.median(values)),
            "minimum": float(np.min(values)),
            "maximum": float(np.max(values)),
        }
    for key in (
        "temporal_difference_abs_p95_p99_p999_p9999",
        "temporal_pixel_std_p50_p90_p99_p999",
        "normalized_nps_bands",
    ):
        values = np.asarray([row[key] for row in ratio_rows], np.float64)
        summary[key] = {
            "median": np.median(values, axis=0).tolist(),
            "minimum": np.min(values, axis=0).tolist(),
            "maximum": np.max(values, axis=0).tolist(),
        }

    result = {
        "reference": str(args.reference),
        "candidate": str(args.candidate),
        "dimensions": [width_a, height_a],
        "frames": frames_a,
        "crop_size": crop_size,
        "nps_band_edges_cycles_per_pixel": NPS_EDGES.tolist(),
        "summary": summary,
        "crops": crops,
        "interpretation_boundary": (
            "These are perceptual diagnostics, not published 5279 acceptance limits. "
            "Ratios should be judged across scenes and against reference seed variation."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
