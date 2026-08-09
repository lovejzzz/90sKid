#!/usr/bin/env python3
"""Validate V31's normal-process chroma/tone correction on three scenes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np


CLIPS = ("T002", "T020", "T032")
MASTER = "05_emulsion_master_prores4444.mov"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries",
            "stream=codec_name,profile,width,height,nb_frames,pix_fmt,bits_per_raw_sample,color_space,color_transfer,color_primaries",
            "-of", "json", str(path),
        ],
        text=True,
    )
    return json.loads(payload)["streams"][0]


def preview(path: Path, frame: int = 12) -> np.ndarray:
    width, height = 960, 720
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path),
            "-vf", f"select=eq(n\\,{frame}),scale={width}:{height}:flags=area",
            "-frames:v", "1", "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ]
    )
    return (
        np.frombuffer(payload, dtype="<u2")
        .reshape(height, width, 3)
        .astype(np.float32)
        / 65535.0
    )


def rec709_decode(signal: np.ndarray) -> np.ndarray:
    return np.where(
        signal < 0.081,
        signal / 4.5,
        np.power((signal + 0.099) / 1.099, 1.0 / 0.45),
    ).astype(np.float32)


def oklab(linear: np.ndarray) -> np.ndarray:
    l = np.cbrt(np.maximum(
        0.4122214708 * linear[..., 0]
        + 0.5363325363 * linear[..., 1]
        + 0.0514459929 * linear[..., 2], 0.0
    ))
    m = np.cbrt(np.maximum(
        0.2119034982 * linear[..., 0]
        + 0.6806995451 * linear[..., 1]
        + 0.1073969566 * linear[..., 2], 0.0
    ))
    s = np.cbrt(np.maximum(
        0.0883024619 * linear[..., 0]
        + 0.2817188376 * linear[..., 1]
        + 0.6299787005 * linear[..., 2], 0.0
    ))
    return np.stack(
        [
            0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
        ],
        axis=-1,
    )


def perceptual_metrics(signal: np.ndarray) -> dict[str, float]:
    linear = rec709_decode(signal)
    lab = oklab(linear)
    chroma = np.linalg.norm(lab[..., 1:3], axis=-1)
    useful = (lab[..., 0] > 0.10) & (lab[..., 0] < 0.90)
    luma = np.einsum("...c,c->...", linear, [0.2126, 0.7152, 0.0722])
    high = luma - cv2.GaussianBlur(
        luma, (0, 0), 1.2, borderType=cv2.BORDER_REFLECT
    )
    texture = (luma > 0.02) & (luma < 0.65)
    return {
        "median_oklab_chroma": float(np.median(chroma[useful])),
        "p90_oklab_chroma": float(np.percentile(chroma[useful], 90.0)),
        "median_oklab_saturation": float(
            np.median(chroma[useful] / np.maximum(lab[..., 0][useful], 1e-6))
        ),
        "median_oklab_lightness": float(np.median(lab[..., 0])),
        "p90_minus_p10_linear_luma": float(
            np.percentile(luma, 90.0) - np.percentile(luma, 10.0)
        ),
        "fine_luma_texture_rms": float(np.sqrt(np.mean(high[texture] ** 2))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    parser.add_argument("v30_release", type=Path)
    args = parser.parse_args()

    failures: list[str] = []
    report: dict[str, object] = {"release": str(args.release), "clips": {}}
    for clip in CLIPS:
        current = args.release / clip
        previous = args.v30_release / clip
        projection = current / "projection" / MASTER
        scan = current / "bluray_scan" / MASTER
        v30_projection = previous / "projection" / MASTER
        v30_scan = previous / "bluray_scan" / MASTER

        metadata = probe(projection)
        format_checks = {
            "native_dimensions": [metadata.get("width"), metadata.get("height")]
            == [5760, 4320],
            "twenty_four_frames": int(metadata.get("nb_frames", 0)) == 24,
            "prores_4444": metadata.get("codec_name") == "prores"
            and metadata.get("profile") == "4444",
            "twelve_bit": metadata.get("pix_fmt") == "yuv444p12le"
            and int(metadata.get("bits_per_raw_sample", 0)) == 12,
            "rec709_111": metadata.get("color_primaries") == "bt709"
            and metadata.get("color_transfer") == "bt709"
            and metadata.get("color_space") == "bt709",
        }
        failures.extend(
            f"{clip}:format:{name}"
            for name, passed in format_checks.items()
            if not passed
        )

        images = {
            "v31_projection": preview(projection),
            "v31_scan": preview(scan),
            "v30_projection": preview(v30_projection),
        }
        metrics = {name: perceptual_metrics(image) for name, image in images.items()}
        p31 = metrics["v31_projection"]
        s31 = metrics["v31_scan"]
        p30 = metrics["v30_projection"]
        ratios = {
            "v31_projection_to_scan_median_chroma": (
                p31["median_oklab_chroma"] / s31["median_oklab_chroma"]
            ),
            "v30_projection_to_scan_median_chroma": (
                p30["median_oklab_chroma"] / s31["median_oklab_chroma"]
            ),
            "v31_projection_to_scan_median_saturation": (
                p31["median_oklab_saturation"]
                / s31["median_oklab_saturation"]
            ),
            "v30_projection_to_scan_median_saturation": (
                p30["median_oklab_saturation"]
                / s31["median_oklab_saturation"]
            ),
            "v31_to_v30_fine_luma_texture": (
                p31["fine_luma_texture_rms"] / p30["fine_luma_texture_rms"]
            ),
        }
        process_checks = {
            "scan_is_bit_identical_to_v30": sha256(scan) == sha256(v30_scan),
            "absolute_chroma_is_not_silver_suppressed": (
                ratios["v31_projection_to_scan_median_chroma"] >= 0.88
            ),
            "chroma_retention_improves_over_v30": (
                ratios["v31_projection_to_scan_median_chroma"]
                > ratios["v30_projection_to_scan_median_chroma"] + 0.01
            ),
            "saturation_is_not_silver_suppressed": (
                ratios["v31_projection_to_scan_median_saturation"] >= 0.94
            ),
            "saturation_retention_improves_over_v30": (
                ratios["v31_projection_to_scan_median_saturation"]
                > ratios["v30_projection_to_scan_median_saturation"] + 0.025
            ),
            "projection_lightness_is_preserved": abs(
                p31["median_oklab_lightness"] - p30["median_oklab_lightness"]
            ) < 0.004,
            "projection_texture_is_preserved": (
                0.96 <= ratios["v31_to_v30_fine_luma_texture"] <= 1.04
            ),
        }
        failures.extend(
            f"{clip}:process:{name}"
            for name, passed in process_checks.items()
            if not passed
        )
        report["clips"][clip] = {
            "projection_metadata": metadata,
            "format_checks": format_checks,
            "metrics": metrics,
            "ratios": ratios,
            "process_checks": process_checks,
        }

    report["passed"] = not failures
    report["failures"] = failures
    destination = args.release / "validation.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": not failures, "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
