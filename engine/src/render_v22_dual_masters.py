#!/usr/bin/env python3
"""Render V22 projection-monitor and Blu-ray scan masters from one emulsion."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_still(path: Path, bt709: np.ndarray) -> None:
    display = e.srgb_encode(e.bt709_decode(bt709))
    image = np.rint(np.clip(display, 0.0, 1.0) * 255.0).astype(np.uint8)
    cv2.imwrite(
        str(path),
        cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
        [cv2.IMWRITE_JPEG_QUALITY, 96],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument("--oversample", type=int, default=1)
    args = parser.parse_args()

    width, height, fps = e.probe_video(args.input)
    projection_dir = args.output / "projection"
    scan_dir = args.output / "bluray_scan"
    projection_dir.mkdir(parents=True, exist_ok=True)
    scan_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "projection": projection_dir / "05_emulsion_master_prores4444.mov",
        "scan": scan_dir / "05_emulsion_master_prores4444.mov",
    }
    encoders = {
        name: subprocess.Popen(
            e.prores_encoder_command(path, width, height, fps),
            stdin=subprocess.PIPE,
        )
        for name, path in paths.items()
    }
    decoder = subprocess.Popen(
        [
            str(args.decoder),
            str(args.input),
            str(args.start_frame),
            str(args.frames),
        ],
        stdout=subprocess.PIPE,
    )
    assert decoder.stdout is not None
    frame_bytes = width * height * 3 * 4
    representative_index = args.frames // 2
    representative: dict[str, np.ndarray] = {}
    processed = 0
    while processed < args.frames:
        payload = decoder.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            break
        raw = np.frombuffer(payload, dtype="<f4").reshape(height, width, 3)
        film = e.scene_to_5279_film_rgb(
            raw,
            exposure_stops=args.exposure_stops,
            raw_colour="panasonic_official",
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.film_records_from_rgb(film)
        mean_density = e.develop_5279_record_density(records)
        frame_number = args.start_frame + processed
        formed_density = e.form_5279_multilayer_record_density(
            records,
            frame_number,
            args.grain_scale,
            args.oversample,
        )
        outputs = {
            "projection": e.reconstruct_density_pair_to_display(
                mean_density,
                formed_density,
                frame_number,
                args.grain_scale,
                "2383_projection_monitor",
            ),
            "scan": e.reconstruct_density_pair_to_display(
                mean_density,
                formed_density,
                frame_number,
                args.grain_scale,
                "cineon_bluray",
            ),
        }
        for name, image in outputs.items():
            encoded = np.rint(np.clip(image, 0.0, 1.0) * 65535.0).astype("<u2")
            assert encoders[name].stdin is not None
            encoders[name].stdin.write(encoded.tobytes())
        if processed == representative_index:
            representative = {name: image.copy() for name, image in outputs.items()}
        processed += 1
        print(f"processed shared-emulsion frame {processed}/{args.frames}", flush=True)

    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError("ProRes RAW decoder failed")
    if processed != args.frames:
        raise RuntimeError(f"decoded {processed} frames; expected {args.frames}")
    for name, encoder in encoders.items():
        assert encoder.stdin is not None
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f"{name} encoder failed")
        e.finalize_prores_rec709_metadata(paths[name])

    for name, image in representative.items():
        directory = projection_dir if name == "projection" else scan_dir
        save_still(directory / "still_emulsion.jpg", image)

    common = {
        "release": "V22 research candidate",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "input_dimensions": [width, height],
        "fps": fps,
        "start_frame": args.start_frame,
        "frames_processed": processed,
        "input_decode": "Apple extended-linear BT.2020 RGB float32",
        "raw_colour_transform": "Panasonic official GH7-compatible ProRes RAW camera LUT",
        "exposure_stops": args.exposure_stops,
        "grain_scale": args.grain_scale,
        "oversample": args.oversample,
        "shared_emulsion_realization": True,
        "algorithm_sha256": sha256(Path(e.__file__)),
        "d60_relative_chroma_lut": str(e.PRINT_2383_D60_RELATIVE_CHROMA_DELTA_PATH),
        "d60_relative_chroma_lut_sha256": sha256(
            e.PRINT_2383_D60_RELATIVE_CHROMA_DELTA_PATH
        ),
    }
    manifests = {
        "projection": {
            **common,
            "viewing_look": "2383_projection_monitor",
            "colour_scope": "analytical-dye 2383 physical lightness plus neutral-preserving D60-relative monitor chroma proof",
            "master_sha256": sha256(paths["projection"]),
        },
        "scan": {
            **common,
            "viewing_look": "cineon_bluray",
            "colour_scope": "period Spirit-style negative scan and restrained Blu-ray lower-scale finish; no 2383 print colour",
            "master_sha256": sha256(paths["scan"]),
        },
    }
    for name, manifest in manifests.items():
        directory = projection_dir if name == "projection" else scan_dir
        (directory / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )


if __name__ == "__main__":
    main()
