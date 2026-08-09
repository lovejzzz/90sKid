#!/usr/bin/env python3
"""Decode representative frames from the two V23 sources and render a V22 baseline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import emulsion_experiment as e  # noqa: E402

DECODER = Path("/tmp/prores_raw_float_decode")
SOURCES = [
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"),
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T032.MOV"),
]
SAMPLE_FRAMES = [0, 36, 71]
OUT = Path(__file__).resolve().parent / "v22_baseline"


def decode(path: Path, frame: int) -> np.ndarray:
    width, height, _ = e.probe_video(path)
    result = subprocess.run(
        [str(DECODER), str(path), str(frame), "1"],
        stdout=subprocess.PIPE,
        check=True,
    )
    expected = width * height * 3 * 4
    if len(result.stdout) != expected:
        raise RuntimeError(f"decoder returned {len(result.stdout)} bytes, expected {expected}")
    return np.frombuffer(result.stdout, dtype="<f4").reshape(height, width, 3)


def jpeg(path: Path, bt709: np.ndarray) -> None:
    srgb = e.srgb_encode(e.bt709_decode(bt709))
    u8 = np.rint(np.clip(srgb, 0.0, 1.0) * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(u8, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 94])


def stats(image: np.ndarray) -> dict[str, object]:
    luma = image @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    spread = np.max(image, axis=-1) - np.min(image, axis=-1)
    return {
        "luma_percentiles": np.percentile(luma, [0, 1, 10, 50, 90, 99, 99.9, 100]).tolist(),
        "rgb_percentiles": np.percentile(image, [0.1, 1, 50, 99, 99.9]).tolist(),
        "median_channel_spread": float(np.median(spread)),
        "fraction_any_zero": float(np.mean(np.any(image <= 0.0, axis=-1))),
        "fraction_any_one": float(np.mean(np.any(image >= 1.0, axis=-1))),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {}
    for source in SOURCES:
        stem = source.stem.split("_")[-1].lower()
        rows: list[np.ndarray] = []
        source_report: dict[str, object] = {}
        for frame_number in SAMPLE_FRAMES:
            raw = decode(source, frame_number)
            raw_small = cv2.resize(raw, (1440, 1080), interpolation=cv2.INTER_AREA)
            film = e.scene_to_5279_film_rgb(
                raw_small,
                exposure_stops=0.45,
                raw_colour="panasonic_official",
                include_optical_scatter=True,
                sensor_noise_treatment="photochemical",
            )
            records = e.film_records_from_rgb(film)
            mean_density = e.develop_5279_record_density(records)
            formed = e.form_5279_multilayer_record_density(records, frame_number, 1.0, 1)
            projection = e.reconstruct_density_pair_to_display(
                mean_density, formed, frame_number, 1.0, "2383_projection_monitor"
            )
            scan = e.reconstruct_density_pair_to_display(
                mean_density, formed, frame_number, 1.0, "cineon_bluray"
            )
            jpeg(OUT / f"{stem}_f{frame_number:03d}_projection.jpg", projection)
            jpeg(OUT / f"{stem}_f{frame_number:03d}_scan.jpg", scan)
            label = np.full((44, 2880, 3), 0.018, np.float32)
            cv2.putText(label, f"{stem.upper()}  F{frame_number:03d}  PROJECTION | SCAN", (20, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0.75, 0.75, 0.75), 1, cv2.LINE_AA)
            rows.append(np.concatenate([label, np.concatenate([projection, scan], axis=1)], axis=0))
            source_report[str(frame_number)] = {
                "raw_min_max": [float(raw.min()), float(raw.max())],
                "projection": stats(projection),
                "scan": stats(scan),
            }
        contact = np.concatenate(rows, axis=0)
        jpeg(OUT / f"{stem}_contact.jpg", contact)
        report[stem] = source_report
    (OUT / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
