#!/usr/bin/env python3
"""Measure FSD against the V40 physical-density residual.

The deterministic branch is the common mean image.  Measurements are made in
display-linear Rec.709 from the sRGB companion, so codec/gamma differences do
not get mistaken for grain energy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e


LUMA = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
VALID_SUPPORT_BORDER = 2


def probe(path: Path) -> tuple[int, int]:
    record = json.loads(
        subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "json", str(path),
            ]
        )
    )["streams"][0]
    return int(record["width"]), int(record["height"])


def decode_srgb_frame(path: Path, frame: int) -> np.ndarray:
    width, height = probe(path)
    command = [
        "ffmpeg", "-v", "error", "-i", str(path), "-an", "-vf",
        (
            "setparams=color_primaries=bt709:color_trc=iec61966-2-1:"
            f"colorspace=bt709,select=eq(n\\,{frame})"
        ),
        "-frames:v", "1", "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
    ]
    payload = subprocess.check_output(command)
    expected = width * height * 3 * 2
    if len(payload) != expected:
        raise RuntimeError(f"short decode for {path}: {len(payload)} != {expected}")
    encoded = np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)
    return e.srgb_decode(encoded.astype(np.float32) / 65535.0)


def lag_correlation(field: np.ndarray, axis: int) -> float:
    centered = field - field.mean(dtype=np.float64)
    if axis == 1:
        a, b = centered[:, :-1], centered[:, 1:]
    else:
        a, b = centered[:-1], centered[1:]
    denominator = np.sqrt(
        np.mean(np.square(a), dtype=np.float64)
        * np.mean(np.square(b), dtype=np.float64)
    )
    return float(np.mean(a * b, dtype=np.float64) / max(denominator, 1.0e-15))


def radial_spectrum(field: np.ndarray) -> dict[str, float]:
    # Downsample-free, windowed central crop keeps the frequency comparison
    # fast while preserving native-pixel morphology.
    size = min(2048, field.shape[0], field.shape[1])
    y0 = (field.shape[0] - size) // 2
    x0 = (field.shape[1] - size) // 2
    crop = field[y0:y0 + size, x0:x0 + size].astype(np.float64)
    crop -= crop.mean()
    window = np.hanning(size)
    transform = np.fft.rfft2(crop * window[:, None] * window[None, :])
    power = np.square(np.abs(transform))
    fy = np.fft.fftfreq(size)[:, None]
    fx = np.fft.rfftfreq(size)[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    total = float(power.sum())
    if total <= 0.0:
        return {"low_0_005_0_03": 0.0, "mid_0_03_0_15": 0.0, "high_0_15_0_5": 0.0}
    return {
        "low_0_005_0_03": float(power[(radius >= 0.005) & (radius < 0.03)].sum() / total),
        "mid_0_03_0_15": float(power[(radius >= 0.03) & (radius < 0.15)].sum() / total),
        "high_0_15_0_5": float(power[(radius >= 0.15) & (radius <= 0.5)].sum() / total),
    }


def metrics(candidate: np.ndarray, baseline: np.ndarray) -> dict[str, object]:
    # The observer's median radius 1 plus neighbourhood radius 1 leaves a
    # two-pixel invalid support perimeter.  Including it can turn convolution
    # padding into an apparent near-white stochastic tail, especially on the
    # final row, even though that perimeter is excluded by the V40 release gate.
    border = VALID_SUPPORT_BORDER
    candidate = candidate[border:-border, border:-border]
    baseline = baseline[border:-border, border:-border]
    delta_rgb = candidate - baseline
    delta = np.einsum("...c,c->...", delta_rgb, LUMA, optimize=True).astype(np.float32)
    absolute = np.abs(delta)
    highpass = delta - cv2.GaussianBlur(delta, (0, 0), 1.0)
    opponent = delta_rgb - delta[..., None]
    return {
        "luma_delta_mean": float(delta.mean(dtype=np.float64)),
        "luma_delta_rms": float(np.sqrt(np.mean(np.square(delta), dtype=np.float64))),
        "luma_delta_p990_abs": float(np.quantile(absolute, 0.99)),
        "luma_delta_p999_abs": float(np.quantile(absolute, 0.999)),
        "luma_delta_max_abs": float(absolute.max()),
        "highpass_rms_sigma1": float(np.sqrt(np.mean(np.square(highpass), dtype=np.float64))),
        "lag1_x": lag_correlation(delta, 1),
        "lag1_y": lag_correlation(delta, 0),
        "opponent_delta_rms": float(np.sqrt(np.mean(np.square(opponent), dtype=np.float64))),
        "radial_power_fraction": radial_spectrum(delta),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical", type=Path, required=True)
    parser.add_argument("--deterministic", type=Path, required=True)
    parser.add_argument("--fsd", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--site-count", type=int, default=1600)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    deterministic = decode_srgb_frame(args.deterministic, args.frame)
    physical = decode_srgb_frame(args.physical, args.frame)
    fsd = decode_srgb_frame(args.fsd, args.frame)
    physical_metrics = metrics(physical, deterministic)
    fsd_metrics = metrics(fsd, deterministic)
    ratio = fsd_metrics["luma_delta_rms"] / physical_metrics["luma_delta_rms"]
    record = {
        "measurement_space": "display-linear Rec.709 decoded from sRGB companion",
        "valid_support_border_pixels": VALID_SUPPORT_BORDER,
        "frame": args.frame,
        "physical_v40_minus_deterministic": physical_metrics,
        "fsd_minus_deterministic": fsd_metrics,
        "fsd_to_physical_luma_rms_ratio": float(ratio),
        "rms_matched_site_count_estimate": max(2, int(round(args.site_count * ratio * ratio))),
    }
    payload = json.dumps(record, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
