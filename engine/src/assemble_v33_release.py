#!/usr/bin/env python3
"""Assemble V33 from the byte-frozen V31/V32 image masters."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from render_v23_dual_masters import sha256
import v33_profile


SCENES = {
    "T002": {
        "start_frame": 0,
        "source": "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV",
        "projection": "outputs/native_5k_v31_final_1s/T002/projection/05_emulsion_master_prores4444.mov",
        "scan": "outputs/native_5k_v31_final_1s/T002/bluray_scan/05_emulsion_master_prores4444.mov",
        "film_ei": "outputs/native_5k_v31_final_1s/T002/camera_baseline/05_camera_baseline_prores4444.mov",
    },
    "T007": {
        "start_frame": 276,
        "source": "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T007.MOV",
        "projection": "outputs/native_5k_v32_measurement_1s/T007/projection/05_emulsion_master_prores4444.mov",
        "scan": "outputs/native_5k_v32_measurement_1s/T007/bluray_scan/05_emulsion_master_prores4444.mov",
        "film_ei": "outputs/native_5k_v32_measurement_1s/T007/camera_baseline/05_camera_baseline_prores4444.mov",
    },
    "T031": {
        "start_frame": 132,
        "source": "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T031.MOV",
        "projection": "outputs/native_5k_v32_measurement_1s/T031/projection/05_emulsion_master_prores4444.mov",
        "scan": "outputs/native_5k_v32_measurement_1s/T031/bluray_scan/05_emulsion_master_prores4444.mov",
        "film_ei": "outputs/native_5k_v32_measurement_1s/T031/camera_baseline/05_camera_baseline_prores4444.mov",
    },
}


def replace_symlink(destination: Path, source: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or destination.exists():
        destination.unlink()
    destination.symlink_to(os.path.relpath(source.resolve(), destination.parent.resolve()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    project = Path(__file__).resolve().parents[1]
    records: dict[str, object] = {}
    for scene, values in SCENES.items():
        branches = {
            "projection": Path(values["projection"]),
            "bluray_scan": Path(values["scan"]),
            "camera_filmei_plus045": Path(values["film_ei"]),
        }
        scene_records: dict[str, object] = {}
        for branch, relative_source in branches.items():
            source = (project / relative_source).resolve()
            filename = (
                "05_camera_baseline_prores4444.mov"
                if branch.startswith("camera_")
                else "05_emulsion_master_prores4444.mov"
            )
            destination = args.output / scene / branch / filename
            replace_symlink(destination, source)
            scene_records[branch] = {
                "path": str(destination),
                "frozen_source": str(source),
                "sha256": sha256(source),
            }
        records[scene] = {
            "source": values["source"],
            "start_frame": values["start_frame"],
            "frames": 24,
            "branches": scene_records,
        }
    manifest = {
        "release": v33_profile.PROFILE["name"],
        "profile": v33_profile.PROFILE,
        "image_change": "none; links resolve to accepted byte-frozen V31/V32 masters",
        "scenes": records,
    }
    (args.output / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
