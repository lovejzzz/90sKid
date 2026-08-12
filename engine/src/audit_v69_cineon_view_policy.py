#!/usr/bin/env python3
"""Audit DPX-pure view policies against the historical managed scan branch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import cv2
import numpy as np

from engine.emulsion5279.contracts import EngineConfig, EngineMode
from engine.emulsion5279.io import (
    ProResRawDecoder,
    rebuild_srgb_companion_from_master,
)
from engine.emulsion5279.pipeline import Emulsion5279Engine
from engine.emulsion5279.view_policy import (
    CineonViewPolicy,
    LEGACY_MANAGED_SCAN_CONTRACT,
    POLICY_CONTRACTS,
)
from engine.emulsion5279 import legacy


def encode_one_frame_master(path: Path, linear: np.ndarray, fps: str) -> None:
    height, width = linear.shape[:2]
    path.parent.mkdir(parents=True, exist_ok=True)
    command = legacy.model.prores_encoder_command(path, width, height, fps)
    command[command.index("-profile:v") + 1] = "5"
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if process.stdin is None:
        raise RuntimeError("failed to open ProRes encoder")
    encoded = legacy.model.bt1886_reference_encode(linear)
    process.stdin.write(
        np.rint(np.clip(encoded, 0.0, 1.0) * 65535.0)
        .astype("<u2")
        .tobytes()
    )
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError(f"failed to encode {path}")
    legacy.model.finalize_prores_rec709_metadata(path)


def decoded_md5(path: Path) -> str:
    result = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1",
            "-pix_fmt", "yuv444p12le", "-f", "md5", "-",
        ],
        text=True,
    ).strip()
    return result.removeprefix("MD5=")


def oklab_summary(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    e = legacy.model
    delta = e.linear_rec709_to_oklab(candidate) - e.linear_rec709_to_oklab(reference)
    distance = np.sqrt(np.sum(delta * delta, axis=-1))
    absolute = np.abs(candidate - reference)
    return {
        "linear_rgb_mae": float(np.mean(absolute)),
        "linear_rgb_p95_abs": float(np.percentile(absolute, 95)),
        "linear_rgb_p99_abs": float(np.percentile(absolute, 99)),
        "oklab_median": float(np.median(distance)),
        "oklab_p95": float(np.percentile(distance, 95)),
        "oklab_p99": float(np.percentile(distance, 99)),
    }


def structure_summary(image: np.ndarray) -> dict[str, float]:
    luma_weights = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    low = cv2.GaussianBlur(image, (0, 0), 1.55, borderType=cv2.BORDER_REFLECT)
    high = image - low
    luma = np.einsum("...c,c->...", high, luma_weights)
    opponent = high - luma[..., None]
    return {
        "highpass_luma_rms": float(np.sqrt(np.mean(luma * luma))),
        "highpass_opponent_rms": float(np.sqrt(np.mean(opponent * opponent))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--review-width", type=int, default=1920)
    args = parser.parse_args()

    started = time.perf_counter()
    engine = Emulsion5279Engine(
        EngineConfig(profile="v66", mode=EngineMode.PRODUCTION_METAL)
    )
    with ProResRawDecoder(args.decoder, args.source, args.frame, 1) as decoder:
        absolute_frame, raw = next(iter(decoder))
        rendered = engine.render_frame(raw, absolute_frame)
        if rendered.cineon_printing_density_code is None:
            raise RuntimeError("render produced no Cineon code")
        legacy_managed = rendered.observers.scan_linear_rec709
        open_monitor = engine.view_cineon_data(
            rendered.cineon_printing_density_code,
            CineonViewPolicy.OPEN_MONITOR_V66,
        )
        pointwise = engine.view_cineon_data(
            rendered.cineon_printing_density_code,
            CineonViewPolicy.BLURAY_POINTWISE_V66,
        )
        fps = decoder.fps
    engine.validate_rendered_frames(1)

    branches = {
        "cineon_open_monitor": open_monitor,
        "cineon_bluray_pointwise": pointwise,
        "legacy_managed_bluray": legacy_managed,
    }
    files: dict[str, dict[str, str]] = {}
    for name, image in branches.items():
        root = args.output / name
        master = root / "05_emulsion_master_prores4444.mov"
        preview = root / "06_quicktime_preview_srgb_prores4444.mov"
        encode_one_frame_master(master, image, fps)
        rebuild_srgb_companion_from_master(master, preview, 1)
        files[name] = {
            "master": str(master),
            "preview": str(preview),
            "still": str(root / "still_emulsion.jpg"),
            "decoded_master_md5": decoded_md5(master),
        }

    height, width = legacy_managed.shape[:2]
    review_width = min(int(args.review_width), width)
    review_height = max(2, round(height * review_width / width))
    review = {
        name: cv2.resize(
            image, (review_width, review_height), interpolation=cv2.INTER_AREA
        ).astype(np.float32)
        for name, image in branches.items()
    }
    crop_size = min(1024, height, width)
    y0 = (height - crop_size) // 2
    x0 = (width - crop_size) // 2
    native_crop = {
        name: image[y0 : y0 + crop_size, x0 : x0 + crop_size]
        for name, image in branches.items()
    }
    luma_weights = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    luma = {
        name: np.einsum("...c,c->...", image, luma_weights)
        for name, image in review.items()
    }
    code = rendered.cineon_printing_density_code
    report = {
        "audit": "V69 named Cineon view-policy ownership",
        "classification": "delivery/view architecture; no 5279 profile promoted",
        "source": str(args.source),
        "absolute_frame": int(absolute_frame),
        "dimensions": [width, height],
        "cineon_code_md5": hashlib.md5(code.tobytes()).hexdigest(),
        "policies": {
            policy.value: contract for policy, contract in POLICY_CONTRACTS.items()
        },
        "legacy_managed_contract": LEGACY_MANAGED_SCAN_CONTRACT,
        "files": files,
        "review_metrics_1920": {
            "pointwise_vs_legacy_managed": oklab_summary(
                review["legacy_managed_bluray"],
                review["cineon_bluray_pointwise"],
            ),
            "open_vs_pointwise_finish": oklab_summary(
                review["cineon_open_monitor"],
                review["cineon_bluray_pointwise"],
            ),
            "luma_median": {
                name: float(np.median(values)) for name, values in luma.items()
            },
            "luma_p99": {
                name: float(np.percentile(values, 99))
                for name, values in luma.items()
            },
        },
        "native_centre_crop_structure": {
            name: structure_summary(image) for name, image in native_crop.items()
        },
        "render_stage_seconds": dict(rendered.stage_seconds),
        "wall_seconds": time.perf_counter() - started,
        "interpretation": (
            "The historical managed scan is not reconstructible from one DPX "
            "frame because it also consumes the deterministic mean observer. "
            "The two named V69 policies are pure functions of DPX data."
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
