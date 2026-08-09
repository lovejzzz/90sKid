#!/usr/bin/env python3
"""Validate V33 input, exposure, low-end, gamma and delivery boundaries."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

import emulsion_experiment as e
from render_v23_dual_masters import sha256
from render_v30_camera_baseline import (
    V709_LEGAL_BLACK,
    V709_LEGAL_WHITE,
    load_cube,
)
import v33_profile


SCENES = ("T002", "T007", "T031")
FRAMES = 24
WIDTH, HEIGHT = 960, 720
FCP_WITNESS = (
    Path(__file__).resolve().parents[1]
    / "research_runs/2026-08-05_fcp_full_pipeline_audit/fcp_reference/"
    "FCP_Standard_T031_frame144_1s.mov"
)


def probe(path: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries",
            "stream=codec_name,profile,width,height,nb_frames,pix_fmt,bits_per_raw_sample,color_space,color_transfer,color_primaries,avg_frame_rate",
            "-of", "json", str(path),
        ],
        text=True,
    )
    return json.loads(payload)["streams"][0]


def decode(path: Path) -> np.ndarray:
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-an",
            "-vf", f"scale={WIDTH}:{HEIGHT}:flags=area", "-frames:v", str(FRAMES),
            "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ]
    )
    values = np.frombuffer(payload, dtype="<u2")
    expected = FRAMES * WIDTH * HEIGHT * 3
    if values.size != expected:
        raise RuntimeError(f"{path}: decoded {values.size}; expected {expected}")
    return values.reshape(FRAMES, HEIGHT, WIDTH, 3).astype(np.float32) / 65535.0


def rec709_decode(signal: np.ndarray) -> np.ndarray:
    return np.where(
        signal < 0.081,
        signal / 4.5,
        np.power((signal + 0.099) / 1.099, 1.0 / 0.45),
    ).astype(np.float32)


def luma(linear: np.ndarray) -> np.ndarray:
    return np.einsum("...c,c->...", linear, [0.2126, 0.7152, 0.0722])


def format_checks(metadata: dict[str, object]) -> dict[str, bool]:
    return {
        "native_5760x4320": [metadata.get("width"), metadata.get("height")] == [5760, 4320],
        "source_rate_24000_1001": metadata.get("avg_frame_rate") == "24000/1001",
        "twenty_four_frames": int(metadata.get("nb_frames", 0)) == FRAMES,
        "prores_4444_12bit": (
            metadata.get("codec_name") == "prores"
            and metadata.get("profile") == "4444"
            and metadata.get("pix_fmt") == "yuv444p12le"
            and int(metadata.get("bits_per_raw_sample", 0)) == 12
        ),
        "rec709_111": (
            metadata.get("color_primaries") == "bt709"
            and metadata.get("color_transfer") == "bt709"
            and metadata.get("color_space") == "bt709"
        ),
    }


def tone_metrics(signal: np.ndarray) -> dict[str, float]:
    y = luma(rec709_decode(signal))
    encoded_y = np.einsum("...c,c->...", signal, [0.2126, 0.7152, 0.0722])
    positive_toe = (y > 0.0) & (y < 0.01)
    return {
        "display_black_fraction": float(np.mean(encoded_y <= 1.0 / 1023.0)),
        "toe_0_to_1_percent_fraction": float(np.mean(positive_toe)),
        "shadow_below_1_8_percent_fraction": float(np.mean(y < 0.018)),
        "linear_luma_p01": float(np.percentile(y, 1)),
        "linear_luma_p05": float(np.percentile(y, 5)),
        "linear_luma_p50": float(np.percentile(y, 50)),
        "linear_luma_p95": float(np.percentile(y, 95)),
        "linear_luma_p99": float(np.percentile(y, 99)),
        "robust_contrast_span_p95_minus_p05": float(np.percentile(y, 95) - np.percentile(y, 5)),
        "white_clip_fraction": float(np.mean(encoded_y >= 1022.0 / 1023.0)),
    }


def paired_tone_metrics(camera: np.ndarray, observer: np.ndarray) -> dict[str, float | int]:
    x = luma(rec709_decode(camera)).reshape(-1)
    y = luma(rec709_decode(observer)).reshape(-1)
    mask = (x > 0.005) & (x < 0.75) & (y > 0.0005) & (y < 0.95)
    log_x = np.log10(x[mask])
    log_y = np.log10(y[mask])
    slope, intercept = np.polyfit(log_x, log_y, 1)
    edges = np.quantile(x[mask], np.linspace(0.0, 1.0, 33))
    medians = []
    for low, high in zip(edges[:-1], edges[1:]):
        current = mask & (x >= low) & (x <= high)
        medians.append(float(np.median(y[current])))
    negative_steps = int(np.sum(np.diff(medians) < -0.001))
    return {
        "effective_log_luma_power": float(slope),
        "effective_log_luma_intercept": float(intercept),
        "tone_curve_negative_steps": negative_steps,
    }


def neutral_v709_gate() -> dict[str, float | bool]:
    ramp = np.linspace(0.0, 1.0, 1000, dtype=np.float32)
    neutral = np.repeat(ramp[:, None], 3, axis=1)
    vgamut = e.bt2020_to_panasonic_vgamut(neutral)
    vlog = e.vlog_encode(vgamut)
    legal = e.apply_rgb_cube_lut(vlog.reshape(1, -1, 3), load_cube(
        Path(__file__).resolve().parents[1]
        / "references/panasonic_v709/VLog_to_V709_forV35_ver100.cube"
    )).reshape(-1, 3)
    normalized = (legal - V709_LEGAL_BLACK) / (V709_LEGAL_WHITE - V709_LEGAL_BLACK)
    spread = np.max(normalized, axis=1) - np.min(normalized, axis=1)
    maximum = float(np.max(np.abs(spread)))
    return {"maximum_neutral_channel_spread": maximum, "passed": maximum < 0.001}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    failures: list[str] = []
    report: dict[str, object] = {
        "release": str(args.release),
        "profile": v33_profile.PROFILE,
        "fcp_witness": {
            "path": str(FCP_WITNESS),
            "sha256": sha256(FCP_WITNESS),
            "passed": sha256(FCP_WITNESS) == v33_profile.PROFILE["fcp_witness_sha256"],
        },
        "neutral_v709": neutral_v709_gate(),
        "scenes": {},
    }
    if not report["fcp_witness"]["passed"]:
        failures.append("fcp_witness_sha256")
    if not report["neutral_v709"]["passed"]:
        failures.append("neutral_v709_axis")

    for scene in SCENES:
        root = args.release / scene
        paths = {
            "projection": root / "projection/05_emulsion_master_prores4444.mov",
            "scan": root / "bluray_scan/05_emulsion_master_prores4444.mov",
            "camera_as_shot_0stop": root / "camera_as_shot_0stop/05_camera_baseline_prores4444.mov",
            "camera_filmei_plus045": root / "camera_filmei_plus045/05_camera_baseline_prores4444.mov",
        }
        metadata = {name: probe(path) for name, path in paths.items()}
        formats = {name: format_checks(value) for name, value in metadata.items()}
        for branch, checks in formats.items():
            failures.extend(
                f"{scene}:format:{branch}:{name}"
                for name, passed in checks.items() if not passed
            )
        signals = {name: decode(path) for name, path in paths.items()}
        tones = {name: tone_metrics(value) for name, value in signals.items()}
        paired = {
            branch: paired_tone_metrics(signals["camera_filmei_plus045"], signals[branch])
            for branch in ("projection", "scan")
        }
        checks = {
            "zero_stop_is_not_brighter_than_plus045": (
                tones["camera_as_shot_0stop"]["linear_luma_p50"]
                <= tones["camera_filmei_plus045"]["linear_luma_p50"]
                and tones["camera_as_shot_0stop"]["linear_luma_p99"]
                <= tones["camera_filmei_plus045"]["linear_luma_p99"] + 0.002
            ),
            "projection_black_is_bounded": tones["projection"]["display_black_fraction"] < 0.01,
            "scan_black_is_bounded": tones["scan"]["display_black_fraction"] < 0.05,
            "scan_does_not_add_excess_black": (
                tones["scan"]["display_black_fraction"]
                <= tones["projection"]["display_black_fraction"] + 0.05
            ),
            "projection_retains_toe_occupancy": tones["projection"]["toe_0_to_1_percent_fraction"] > 0.0001,
            "scan_retains_toe_occupancy": tones["scan"]["toe_0_to_1_percent_fraction"] > 0.0001,
            "projection_contrast_is_noncollapsed": tones["projection"]["robust_contrast_span_p95_minus_p05"] > 0.08,
            "scan_contrast_is_noncollapsed": tones["scan"]["robust_contrast_span_p95_minus_p05"] > 0.08,
            "projection_tone_mapping_is_monotonic": paired["projection"]["tone_curve_negative_steps"] <= 2,
            "scan_tone_mapping_is_monotonic": paired["scan"]["tone_curve_negative_steps"] <= 2,
            "projection_effective_gamma_is_bounded": 0.45 < paired["projection"]["effective_log_luma_power"] < 2.5,
            "scan_effective_gamma_is_bounded": 0.45 < paired["scan"]["effective_log_luma_power"] < 2.5,
        }
        failures.extend(
            f"{scene}:tone:{name}" for name, passed in checks.items() if not passed
        )
        report["scenes"][scene] = {
            "paths": {name: str(path) for name, path in paths.items()},
            "metadata": metadata,
            "format_checks": formats,
            "tone_metrics": tones,
            "paired_camera_to_observer": paired,
            "checks": checks,
        }
    report["technical_neutral"] = {
        "enabled": False,
        "reason": "awaiting measured gray-card/ColorChecker capture",
        "location_when_authorized": "camera input before 5279 exposure",
        "film_model_unchanged": True,
    }
    report["passed"] = not failures
    report["failures"] = failures
    (args.release / "validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"passed": not failures, "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
