#!/usr/bin/env python3
"""Build official Panasonic V-709 contact sheets from selected RAW frames."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from render_v30_camera_baseline import (
    V709_LEGAL_BLACK,
    V709_LEGAL_WHITE,
    DEFAULT_V709_LUT,
    load_cube,
)


def camera_display(raw: np.ndarray, lut: np.ndarray, exposure: float) -> np.ndarray:
    exposed = raw * np.float32(2.0**exposure)
    vgamut = e.bt2020_to_panasonic_vgamut(exposed)
    vlog = e.vlog_encode(vgamut)
    legal = e.apply_rgb_cube_lut(vlog, lut)
    return np.clip(
        (legal - V709_LEGAL_BLACK) / (V709_LEGAL_WHITE - V709_LEGAL_BLACK),
        0.0,
        1.0,
    ).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frames", required=True)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    args = parser.parse_args()
    indices = [int(value) for value in args.frames.split(",")]
    width, height, _ = e.probe_video(args.input)
    process = subprocess.Popen(
        [str(args.decoder), str(args.input), args.frames],
        stdout=subprocess.PIPE,
    )
    assert process.stdout is not None
    frame_bytes = width * height * 3 * 4
    lut = load_cube(DEFAULT_V709_LUT)
    cells: list[np.ndarray] = []
    for index in indices:
        payload = process.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            raise RuntimeError(f"missing contact frame {index}")
        raw = np.frombuffer(payload, dtype="<f4").reshape(height, width, 3)
        image = camera_display(raw, lut, args.exposure_stops)
        image = cv2.resize(image, (960, 720), interpolation=cv2.INTER_AREA)
        display = np.rint(image[..., ::-1] * 255.0).astype(np.uint8)
        cv2.putText(
            display,
            f"frame {index}",
            (28, 58),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.25,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
        cells.append(display)
    process.stdout.close()
    if process.wait() != 0:
        raise RuntimeError("contact decoder failed")
    if len(cells) % 2:
        cells.append(np.zeros_like(cells[0]))
    rows = [
        np.concatenate(cells[i : i + 2], axis=1)
        for i in range(0, len(cells), 2)
    ]
    sheet = np.concatenate(rows, axis=0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), sheet, [cv2.IMWRITE_JPEG_QUALITY, 94]):
        raise RuntimeError("could not write contact sheet")


if __name__ == "__main__":
    main()
