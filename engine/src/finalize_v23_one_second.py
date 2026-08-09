#!/usr/bin/env python3
"""Finalize 24-frame V23 validation clips from the safely closed partial run."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e

ROOT = Path(__file__).resolve().parents[1]
PARTIAL = ROOT / "outputs" / "native_5k_v23_dual_3s"
OUTPUT = ROOT / "outputs" / "native_5k_v23_dual_1s"
SOURCES = {
    "T020": Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"),
    "T032": Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T032.MOV"),
}
# Monotonic wall-clock values printed by the original two concurrent jobs when
# frame 24 completed, before the user changed the requested validation length.
COMPUTE_TO_FRAME_24_SECONDS = {"T020": 3472.0, "T032": 3551.5}
BRANCHES = {"projection": "2383_projection_monitor", "bluray_scan": "cineon_bluray"}
FPS = "24000/1001"
WIDTH, HEIGHT = 5760, 4320
FRAMES = 24


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_still(master: Path, path: Path) -> None:
    command = [
        "ffmpeg", "-v", "error", "-i", str(master),
        "-vf", "select=eq(n\\,12)", "-vsync", "0", "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "rgb48le", "pipe:1",
    ]
    payload = subprocess.run(command, stdout=subprocess.PIPE, check=True).stdout
    expected = WIDTH * HEIGHT * 3 * 2
    if len(payload) != expected:
        raise RuntimeError(f"representative frame is {len(payload)} bytes, expected {expected}")
    bt709 = np.frombuffer(payload, dtype="<u2").reshape(HEIGHT, WIDTH, 3).astype(np.float32) / 65535.0
    display = e.srgb_encode(e.bt709_decode(bt709))
    image = np.rint(np.clip(display, 0.0, 1.0) * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 96])


def finalize_source(name: str, source: Path) -> dict[str, object]:
    post_start = time.perf_counter()
    input_hash = sha256(source)
    output_paths: dict[str, Path] = {}
    for branch in BRANCHES:
        source_master = PARTIAL / name / branch / "05_emulsion_master_prores4444.mov"
        directory = OUTPUT / name / branch
        directory.mkdir(parents=True, exist_ok=True)
        master = directory / "05_emulsion_master_prores4444.mov"
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-i", str(source_master),
                "-map", "0:v:0", "-frames:v", str(FRAMES), "-c", "copy", str(master),
            ],
            check=True,
        )
        e.finalize_prores_rec709_metadata(master)
        save_still(master, directory / "still_emulsion.jpg")
        output_paths[branch] = master

    master_hashes = {branch: sha256(path) for branch, path in output_paths.items()}
    post_seconds = time.perf_counter() - post_start
    source_seconds = FRAMES / (24000.0 / 1001.0)
    timing = {
        "timing_basis": "time.perf_counter values printed by the concurrent production job at completion of frame 24",
        "compute_to_completed_frame_24_seconds": COMPUTE_TO_FRAME_24_SECONDS[name],
        "compute_to_completed_frame_24_minutes": COMPUTE_TO_FRAME_24_SECONDS[name] / 60.0,
        "post_stop_trim_metadata_stills_and_hash_seconds": post_seconds,
        "rendered_source_seconds": source_seconds,
        "wall_seconds_per_output_second_for_two_masters": COMPUTE_TO_FRAME_24_SECONDS[name] / source_seconds,
        "stage_summaries": None,
        "stage_timing_note": "The user changed the requested duration while the original 72-frame job was live. In-memory per-stage arrays were not serialized on KeyboardInterrupt; total frame-completion wall time is genuine, stage values are intentionally not reconstructed.",
        "execution_note": "The first 24 already completed frames were stream-copied from the safely finalized 25-frame partial MOV; no image samples were re-encoded.",
    }
    (OUTPUT / name / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")

    common = {
        "release": "V23 one-second validation",
        "source": str(source),
        "source_sha256": input_hash,
        "input_dimensions": [WIDTH, HEIGHT],
        "fps": FPS,
        "frames_processed": FRAMES,
        "duration_seconds": source_seconds,
        "input_decode": "Apple extended-linear BT.2020 RGB float32",
        "source_metadata": {"camera": "Panasonic DC-GH7", "iso": 500, "white_balance_kelvin": 5500, "shutter_angle_degrees": 180.0},
        "raw_colour_transform": "Panasonic official GH7-compatible ProRes RAW camera LUT",
        "exposure_stops": 0.45,
        "master": "5760x4320, ProRes 4444, yuv444p12le, Rec.709 1-1-1",
        "shared_emulsion_realization": True,
        "grain_morphology": {
            "model": "five-point log-normal-like dye-cloud quadrature with golden-angle subpixel phases",
            "correlation_scale": e.NEGATIVE_GRAIN_CORRELATION_SCALE,
            "fractions": e.GRAIN_SIZE_CLASS_FRACTIONS.tolist(),
            "radius_factors": e.GRAIN_SIZE_CLASS_RADIUS_FACTORS.tolist(),
            "optical_factors": e.GRAIN_SIZE_CLASS_OPTICAL_FACTORS.tolist(),
            "phase_step_radians": e.GRAIN_SIZE_CLASS_PHASE_STEP_RADIANS,
            "amplitude_constraint": "Kodak 5279 per-record diffuse RMS at 48 micrometre aperture",
        },
        "colour_model": "V22 analytical-dye 2383 and neutral-subtracted D60-relative monitor calibration retained after D55/D60/D65 triad candidate produced no material held-out improvement",
        "algorithm_sha256": sha256(Path(e.__file__)),
        "timing": timing,
    }
    for branch, look in BRANCHES.items():
        directory = OUTPUT / name / branch
        manifest = {**common, "viewing_look": look, "master_sha256": master_hashes[branch]}
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return timing


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    timings = {name: finalize_source(name, source) for name, source in SOURCES.items()}
    concurrent = max(COMPUTE_TO_FRAME_24_SECONDS.values())
    report = {
        "release": "V23 one-second validation",
        "source_jobs_launched_concurrently": True,
        "output_masters": 4,
        "frames_per_source": FRAMES,
        "source_duration_seconds_each": FRAMES / (24000.0 / 1001.0),
        "compute_to_frame_24_seconds": COMPUTE_TO_FRAME_24_SECONDS,
        "approximate_concurrent_compute_wall_seconds": concurrent,
        "approximate_concurrent_compute_wall_minutes": concurrent / 60.0,
        "sources": timings,
    }
    (OUTPUT / "release_timing.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
