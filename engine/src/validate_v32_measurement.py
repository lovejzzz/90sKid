#!/usr/bin/env python3
"""Validate V32 scene generalization, cinema output and OFX ROI parity."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from apply_v31_normal_process_adapter import (
    adapt_frame,
    preserve_luma_and_compress_gamut,
    rec709_decode,
)
from build_v32_dcdm_reference import (
    DCDM_ENCODING_PEAK,
    DCDM_HEIGHT,
    DCDM_REFERENCE_LUMINANCE,
    DCDM_WIDTH,
)


MASTER = "05_emulsion_master_prores4444.mov"
SCENES = ("T007", "T031")


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


def decode_preview(path: Path, frames: int = 24) -> np.ndarray:
    width, height = 960, 720
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-an",
            "-vf", f"scale={width}:{height}:flags=area",
            "-frames:v", str(frames), "-pix_fmt", "rgb48le",
            "-f", "rawvideo", "-",
        ]
    )
    expected = frames * width * height * 3
    values = np.frombuffer(payload, dtype="<u2")
    if values.size != expected:
        raise RuntimeError(f"decoded {values.size} values; expected {expected}")
    return values.reshape(frames, height, width, 3).astype(np.float32) / 65535.0


def decode_full_frame(path: Path, frame: int) -> np.ndarray:
    metadata = probe(path)
    width, height = int(metadata["width"]), int(metadata["height"])
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-an",
            "-vf", f"select='eq(n,{frame})'", "-frames:v", "1",
            "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ]
    )
    values = np.frombuffer(payload, dtype="<u2")
    expected = width * height * 3
    if values.size != expected:
        raise RuntimeError(f"decoded {values.size} values; expected {expected}")
    return values.reshape(height, width, 3).astype(np.float32) / 65535.0


def luma(linear: np.ndarray) -> np.ndarray:
    return np.einsum("...c,c->...", linear, [0.2126, 0.7152, 0.0722])


def temporal_metrics(signal: np.ndarray) -> dict[str, float]:
    linear = rec709_decode(signal)
    frame_luma = luma(linear)
    means = np.mean(frame_luma, axis=(1, 2))
    p99 = np.percentile(frame_luma, 99, axis=(1, 2))
    texture_rms = []
    neutral_ab = []
    for frame in linear:
        current_luma = luma(frame)
        high = current_luma - cv2.GaussianBlur(
            current_luma, (0, 0), 1.2, borderType=cv2.BORDER_REFLECT
        )
        texture_rms.append(float(np.sqrt(np.mean(high**2))))
        lab = e.linear_rec709_to_oklab(frame)
        chroma = np.linalg.norm(lab[..., 1:3], axis=-1)
        mask = (lab[..., 0] > 0.12) & (lab[..., 0] < 0.86) & (chroma < 0.035)
        neutral_ab.append(np.mean(lab[..., 1:3][mask], axis=0))
    neutral_ab_array = np.asarray(neutral_ab)
    return {
        "mean_luma": float(np.mean(means)),
        "mean_luma_cv": float(np.std(means) / max(np.mean(means), 1e-8)),
        "maximum_frame_mean_luma_step": float(np.max(np.abs(np.diff(means)))),
        "mean_p99_luma": float(np.mean(p99)),
        "hard_clip_fraction": float(np.mean(np.max(signal, axis=-1) >= 65534 / 65535)),
        "texture_rms_mean": float(np.mean(texture_rms)),
        "texture_rms_cv": float(np.std(texture_rms) / max(np.mean(texture_rms), 1e-8)),
        "neutral_a_mean": float(np.mean(neutral_ab_array[:, 0])),
        "neutral_b_mean": float(np.mean(neutral_ab_array[:, 1])),
        "neutral_ab_temporal_max_std": float(np.max(np.std(neutral_ab_array, axis=0))),
    }


def adapt_frame_tiled(
    projection_signal: np.ndarray,
    scan_signal: np.ndarray,
    tile: int = 256,
) -> tuple[np.ndarray, dict[str, float | int]]:
    height, width = projection_signal.shape[:2]
    sigma = max(0.72 * width / 2048.0, 0.05)
    halo = int(math.ceil(6.0 * sigma))
    result = np.empty_like(projection_signal)
    for y0 in range(0, height, tile):
        for x0 in range(0, width, tile):
            y1, x1 = min(y0 + tile, height), min(x0 + tile, width)
            ey0, ex0 = max(0, y0 - halo), max(0, x0 - halo)
            ey1, ex1 = min(height, y1 + halo), min(width, x1 + halo)
            projection = rec709_decode(projection_signal[ey0:ey1, ex0:ex1])
            scan = rec709_decode(scan_signal[ey0:ey1, ex0:ex1])
            projection_lab = e.linear_rec709_to_oklab(projection)
            scan_lab = e.linear_rec709_to_oklab(scan)
            projection_low = cv2.GaussianBlur(
                projection_lab[..., 1:3], (0, 0), sigma,
                borderType=cv2.BORDER_REFLECT,
            )
            scan_low = cv2.GaussianBlur(
                scan_lab[..., 1:3], (0, 0), sigma,
                borderType=cv2.BORDER_REFLECT,
            )
            target_lab = projection_lab.copy()
            target_lab[..., 1:3] = scan_low + projection_lab[..., 1:3] - projection_low
            target = e.oklab_to_linear_rec709(target_lab)
            corrected = preserve_luma_and_compress_gamut(target, luma(projection))
            encoded = e.bt709_encode(corrected).astype(np.float32)
            iy0, ix0 = y0 - ey0, x0 - ex0
            result[y0:y1, x0:x1] = encoded[
                iy0 : iy0 + (y1 - y0), ix0 : ix0 + (x1 - x0)
            ]
    return result, {"tile": tile, "sigma": sigma, "halo": halo}


def decode_dcdm_xyz(xyz16_bgr: np.ndarray) -> np.ndarray:
    """Decode nominal-RGB TIFF storage back to linear Rec.709 for QA."""
    code12 = np.right_shift(xyz16_bgr[..., ::-1], 4).astype(np.float32)
    normalized = np.power(code12 / 4095.0, 2.6)
    xyz = normalized * (DCDM_ENCODING_PEAK / DCDM_REFERENCE_LUMINANCE)
    return np.einsum(
        "...c,dc->...d", xyz, e.XYZ_D65_TO_REC709
    ).astype(np.float32)


def validate_dcdm(root: Path, projection_path: Path) -> tuple[dict[str, object], dict[str, float | bool]]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    reel = root / str(manifest["reel"])
    frames = sorted(reel.glob("*.tif"))
    if len(frames) != 24:
        raise RuntimeError(f"{root}: found {len(frames)} DCDM frames; expected 24")
    representative = 12
    stored = cv2.imread(str(frames[representative]), cv2.IMREAD_UNCHANGED)
    if stored is None:
        raise RuntimeError(f"could not decode {frames[representative]}")
    low_bits_zero = bool(np.all(np.bitwise_and(stored, np.uint16(15)) == 0))
    source_linear = rec709_decode(decode_full_frame(projection_path, representative))
    source_active = cv2.resize(
        source_linear, (DCDM_WIDTH, DCDM_HEIGHT), interpolation=cv2.INTER_AREA
    )
    recovered = decode_dcdm_xyz(stored)
    delta = np.abs(recovered - source_active)
    names_match = all(
        path.name == f"{manifest['reel']}.{index:05d}.tif"
        for index, path in enumerate(frames, 1)
    )
    checks = {
        "twenty_four_frames": len(frames) == 24,
        "sequential_filenames": names_match,
        "active_4k_dimensions": list(stored.shape) == [DCDM_HEIGHT, DCDM_WIDTH, 3],
        "sixteen_bit_tiff": stored.dtype == np.uint16,
        "low_four_bits_zero": low_bits_zero,
        "twenty_four_fps": manifest.get("dcdm_frame_rate") == 24,
        "st428_xyz_components": manifest.get("colour_components") == "SMPTE ST 428-1 X' Y' Z'",
    }
    measurements: dict[str, float | bool] = {
        "dcdm_roundtrip_mean_abs_linear_rgb": float(np.mean(delta)),
        "dcdm_roundtrip_p99_abs_linear_rgb": float(np.percentile(delta, 99)),
        "dcdm_roundtrip_max_abs_linear_rgb": float(np.max(delta)),
    }
    return {
        "root": str(root),
        "manifest": manifest,
        "representative_frame": str(frames[representative]),
        "format_checks": checks,
    }, measurements


def format_checks(metadata: dict[str, object]) -> dict[str, bool]:
    checks = {
        "native_dimensions": [metadata.get("width"), metadata.get("height")] == [5760, 4320],
        "twenty_four_frames": int(metadata.get("nb_frames", 0)) == 24,
        "prores_4444": metadata.get("codec_name") == "prores" and metadata.get("profile") == "4444",
        "twelve_bit": metadata.get("pix_fmt") == "yuv444p12le" and int(metadata.get("bits_per_raw_sample", 0)) == 12,
    }
    checks["rec709_111"] = (
        metadata.get("color_primaries") == "bt709"
        and metadata.get("color_transfer") == "bt709"
        and metadata.get("color_space") == "bt709"
    )
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    failures: list[str] = []
    report: dict[str, object] = {"release": str(args.release), "scenes": {}}
    for scene in SCENES:
        root = args.release / scene
        paths = {
            "base_projection": root / "base_v30" / "projection" / MASTER,
            "projection": root / "projection" / MASTER,
            "scan": root / "bluray_scan" / MASTER,
            "camera": root / "camera_baseline" / "05_camera_baseline_prores4444.mov",
        }
        metadata = {name: probe(path) for name, path in paths.items()}
        formats = {
            name: format_checks(value)
            for name, value in metadata.items()
        }
        for branch, checks in formats.items():
            failures.extend(
                f"{scene}:format:{branch}:{name}"
                for name, passed in checks.items() if not passed
            )
        previews = {name: decode_preview(path) for name, path in paths.items()}
        linear_projection = rec709_decode(previews["projection"])
        linear_base = rec709_decode(previews["base_projection"])
        luma_delta = np.abs(luma(linear_projection) - luma(linear_base))
        dcdm, dcdm_measurements = validate_dcdm(
            root / "cinema_dcdm", paths["projection"]
        )
        failures.extend(
            f"{scene}:format:dcdm:{name}"
            for name, passed in dcdm["format_checks"].items() if not passed
        )
        representative = 12
        full = adapt_frame(
            previews["base_projection"][representative],
            previews["scan"][representative],
        )
        tiled, roi = adapt_frame_tiled(
            previews["base_projection"][representative],
            previews["scan"][representative],
        )
        tile_delta = np.abs(full - tiled)
        metrics = {
            name: temporal_metrics(value)
            for name, value in previews.items()
        }
        measurements = {
            "adapter_luma_mean_abs": float(np.mean(luma_delta)),
            "adapter_luma_p99_abs": float(np.percentile(luma_delta, 99)),
            "adapter_luma_max_abs": float(np.max(luma_delta)),
            "ofx_tile_mean_abs_signal": float(np.mean(tile_delta)),
            "ofx_tile_p99_abs_signal": float(np.percentile(tile_delta, 99)),
            "ofx_tile_max_abs_signal": float(np.max(tile_delta)),
            "roi_contract": roi,
            **dcdm_measurements,
        }
        checks = {
            "scan_is_base_byte_identical": sha256(paths["scan"]) == sha256(
                root / "base_v30" / "bluray_scan" / MASTER
            ),
            "adapter_preserves_luma": measurements["adapter_luma_p99_abs"] < 0.004,
            "dcdm_reference_roundtrips": measurements["dcdm_roundtrip_p99_abs_linear_rgb"] < 0.003,
            "ofx_tiled_roi_matches_full_frame": measurements["ofx_tile_p99_abs_signal"] < 0.0005,
            "projection_has_no_new_hard_clip": metrics["projection"]["hard_clip_fraction"]
            <= metrics["base_projection"]["hard_clip_fraction"] + 0.0005,
            "projection_mean_has_no_temporal_jump": metrics["projection"]["maximum_frame_mean_luma_step"] < 0.04,
            "projection_texture_is_temporally_stable": metrics["projection"]["texture_rms_cv"] < 0.15,
            "neutral_axis_has_no_temporal_drift": metrics["projection"]["neutral_ab_temporal_max_std"] < 0.006,
        }
        failures.extend(
            f"{scene}:measurement:{name}"
            for name, passed in checks.items() if not passed
        )
        report["scenes"][scene] = {
            "paths": {name: str(path) for name, path in paths.items()},
            "metadata": metadata,
            "format_checks": formats,
            "temporal_metrics": metrics,
            "measurements": measurements,
            "measurement_checks": checks,
            "cinema_reference": dcdm,
        }
    report["ofx_contract"] = {
        "precision": "float32 scene kernels; 12-bit ProRes interchange",
        "temporal_seed": "absolute source-frame index",
        "scheduler": "host schedules frames; plugin does not add a frame pool",
        "roi": "Gaussian operations request ceil(6*sigma) source halo",
        "static_resources": "immutable LUTs and stock constants may be cached",
        "quality_policy": "Archive Exact remains authoritative if GPU parity fails",
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
