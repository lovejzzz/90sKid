#!/usr/bin/env python3
"""Validate and benchmark the complete V23 monitor-print output lattice."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src" / "emulsion_experiment.py"
DECODER = Path("/tmp/prores_raw_float_decode")
SOURCES = [
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"),
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T032.MOV"),
]
OUT = HERE / "projection_lut_validation"


def load():
    spec = importlib.util.spec_from_file_location("v23_lut_validation", SRC)
    if spec is None or spec.loader is None:
        raise RuntimeError(SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e = load()


def decode(path: Path, frame: int) -> np.ndarray:
    width, height, _ = e.probe_video(path)
    result = subprocess.run(
        [str(DECODER), str(path), str(frame), "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(height, width, 3)
    return cv2.resize(raw, (960, 720), interpolation=cv2.INTER_AREA).astype(np.float32)


def compare(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    absolute = np.abs(candidate - reference)
    delta_e = 100.0 * np.linalg.norm(
        e.linear_rec709_to_oklab(candidate) - e.linear_rec709_to_oklab(reference),
        axis=-1,
    )
    return {
        "mean_absolute_linear_rgb": float(np.mean(absolute)),
        "p99_absolute_linear_rgb": float(np.percentile(absolute, 99)),
        "maximum_absolute_linear_rgb": float(np.max(absolute)),
        "mean_oklab_delta_e": float(np.mean(delta_e)),
        "p95_oklab_delta_e": float(np.percentile(delta_e, 95)),
        "p99_oklab_delta_e": float(np.percentile(delta_e, 99)),
        "maximum_oklab_delta_e": float(np.max(delta_e)),
    }


def random_holdout() -> dict[str, object]:
    rng = np.random.default_rng(5279)
    count = 250_000
    net = rng.uniform(-0.16, e.NEGATIVE_5279_MAX_RECORD_DENSITY, (count, 1, 3)).astype(np.float32)
    density = net + e.SENSITO_DMIN_RGB
    start = time.perf_counter()
    exact = e.render_2383_monitor_projection_from_record_density(density)
    exact_seconds = time.perf_counter() - start
    start = time.perf_counter()
    fast = e.render_2383_monitor_projection_fast_from_record_density(density)
    first_fast_seconds = time.perf_counter() - start
    start = time.perf_counter()
    fast = e.render_2383_monitor_projection_fast_from_record_density(density)
    warm_fast_seconds = time.perf_counter() - start
    return {
        "sample_count": count,
        "comparison": compare(exact, fast),
        "exact_seconds": exact_seconds,
        "first_fast_seconds_including_lut_build": first_fast_seconds,
        "warm_fast_seconds": warm_fast_seconds,
        "warm_speedup": exact_seconds / warm_fast_seconds,
    }


def real_frames() -> dict[str, object]:
    report: dict[str, object] = {}
    for source in SOURCES:
        key = source.stem.split("_")[-1].lower()
        raw = decode(source, 36)
        film = e.scene_to_5279_film_rgb(
            raw,
            exposure_stops=0.45,
            raw_colour="panasonic_official",
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.film_records_from_rgb(film)
        mean = e.develop_5279_record_density(records)
        formed = e.form_5279_multilayer_record_density(records, 36, 1.0, 1)
        row: dict[str, object] = {}
        for name, density in (("mean", mean), ("formed", formed)):
            start = time.perf_counter()
            exact = e.render_2383_monitor_projection_from_record_density(density)
            exact_seconds = time.perf_counter() - start
            start = time.perf_counter()
            fast = e.render_2383_monitor_projection_fast_from_record_density(density)
            fast_seconds = time.perf_counter() - start
            row[name] = {
                "comparison": compare(exact, fast),
                "exact_seconds": exact_seconds,
                "fast_seconds": fast_seconds,
                "speedup": exact_seconds / fast_seconds,
            }
        report[key] = row
    return report


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "lattice_size": 193,
        "method": "exact analytical V22/V23 pointwise renderer tabulated over total 5279 record density",
        "random_density_holdout": random_holdout(),
        "real_source_frames_960x720": real_frames(),
    }
    (OUT / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
