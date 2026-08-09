#!/usr/bin/env python3
"""Test V22 colour on two unseen RAW clips against the Resolve D55/D60/D65 bracket."""

from __future__ import annotations

import gc
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VENDOR_DIR = ROOT / "research_runs" / "2026-08-03_vendor_2383_targets"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(VENDOR_DIR))
import emulsion_experiment as e  # noqa: E402
import run_real_frame_vendor_ab as vendor_ab  # noqa: E402
from analyze_vendor_luts import SOURCES, load_cube  # noqa: E402

DECODER = Path("/tmp/prores_raw_float_decode")
SOURCES_RAW = [
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"),
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T032.MOV"),
]
FRAMES = [0, 36, 71]
OUT = HERE / "colour_generalization_metrics.json"


def decode(path: Path, frame: int) -> np.ndarray:
    width, height, _ = e.probe_video(path)
    result = subprocess.run(
        [str(DECODER), str(path), str(frame), "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    native = np.frombuffer(result.stdout, dtype="<f4").reshape(height, width, 3)
    return cv2.resize(native, (1440, 1080), interpolation=cv2.INTER_AREA).astype(np.float32)


def main() -> None:
    cubes = {
        short: load_cube(SOURCES[f"resolve_rec709_{short}"])
        for short in ("d55", "d60", "d65")
    }
    report: dict[str, object] = {}
    for raw_path in SOURCES_RAW:
        clip = raw_path.stem.split("_")[-1].lower()
        report[clip] = {}
        for frame in FRAMES:
            raw = decode(raw_path, frame)
            film = e.scene_to_5279_film_rgb(
                raw,
                exposure_stops=0.45,
                raw_colour="panasonic_official",
                include_optical_scatter=True,
                sensor_noise_treatment="photochemical",
            )
            density = e.develop_5279_record_density(e.film_records_from_rgb(film))
            del raw, film
            cineon = vendor_ab.continuous_cineon_image(e, density)
            rendered = e.render_2383_monitor_projection_from_record_density(density)
            vendors = {
                short: vendor_ab.gamma24_decode(vendor_ab.sample_cube_image(cube, cineon))
                for short, cube in cubes.items()
            }
            report[clip][str(frame)] = {
                "whitepoint_bracket": vendor_ab.bracket_membership(e, rendered, vendors),
                "comparisons": {
                    short: vendor_ab.compare_to_vendor(e, rendered, image)
                    for short, image in vendors.items()
                },
            }
            del density, cineon, rendered, vendors
            gc.collect()
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
