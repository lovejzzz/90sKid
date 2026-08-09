#!/usr/bin/env python3
"""Benchmark actual V27 Gaussian signatures against a generic Metal kernel."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np


def automatic_kernel_size(sigma: float) -> int:
    size = int(round(float(sigma) * 8.0 + 1.0))
    return max(1, size | 1)


def compare(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    delta = np.abs(reference.astype(np.float32) - candidate.astype(np.float32))
    return {
        "maximum": float(delta.max()),
        "mean": float(delta.mean()),
        "p99_9": float(np.percentile(delta, 99.9)),
        "fraction_above_half_12bit_linear_code": float(
            np.mean(delta > (0.5 / 4095.0))
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--swift-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    trace = json.loads(args.trace.read_text())
    full_entries = [
        entry
        for entry in trace["entries"]
        if entry["shape"][0:2] == [4320, 5760]
    ]
    # Cover the signatures responsible for the great majority of Gaussian time,
    # plus both scalar/RGB and REFLECT/REFLECT_101 paths.
    selected: list[dict[str, object]] = []
    seen: set[tuple[float, int, int]] = set()
    for entry in full_entries:
        channels = 1 if len(entry["shape"]) == 2 else int(entry["shape"][2])
        key = (float(entry["sigma_x"]), int(entry["border_type"]), channels)
        if key in seen:
            continue
        selected.append(entry)
        seen.add(key)
        if len(selected) == 10:
            break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    binary = args.output.parent / "metal_separable_benchmark"
    subprocess.run(
        [
            "swiftc",
            "-O",
            "-framework",
            "Metal",
            str(args.swift_source),
            "-o",
            str(binary),
        ],
        check=True,
    )
    source = np.asarray(np.load(args.input, mmap_mode="r"), dtype=np.float32)
    crop = source[:768, :1024]
    results = []
    with tempfile.TemporaryDirectory(prefix="v27-metal-suite-") as temporary:
        root = Path(temporary)
        full_gray = root / "full_gray.raw"
        full_rgb = root / "full_rgb.raw"
        np.ascontiguousarray(source[..., 0]).tofile(full_gray)
        np.ascontiguousarray(source).tofile(full_rgb)
        crop_gray = root / "crop_gray.raw"
        crop_rgb = root / "crop_rgb.raw"
        np.ascontiguousarray(crop[..., 0]).tofile(crop_gray)
        np.ascontiguousarray(crop).tofile(crop_rgb)

        for index, entry in enumerate(selected):
            sigma = float(entry["sigma_x"])
            border = int(entry["border_type"])
            channels = 1 if len(entry["shape"]) == 2 else int(entry["shape"][2])
            size = automatic_kernel_size(sigma)
            radius = size // 2
            weights = cv2.getGaussianKernel(size, sigma, cv2.CV_32F).reshape(-1)
            weights_path = root / f"weights_{index}.raw"
            weights.tofile(weights_path)
            full_input = full_gray if channels == 1 else full_rgb
            completed = subprocess.run(
                [
                    str(binary),
                    str(full_input),
                    str(weights_path),
                    "-",
                    "5760",
                    "4320",
                    str(channels),
                    str(radius),
                    str(border),
                    "5",
                ],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            )
            metal_timing = json.loads(completed.stdout)

            crop_source = crop[..., 0] if channels == 1 else crop
            started = time.perf_counter()
            reference = cv2.GaussianBlur(
                crop_source,
                (0, 0),
                sigma,
                borderType=border,
            )
            crop_cpu_seconds = time.perf_counter() - started
            metal_output = root / f"metal_crop_{index}.raw"
            subprocess.run(
                [
                    str(binary),
                    str(crop_gray if channels == 1 else crop_rgb),
                    str(weights_path),
                    str(metal_output),
                    "1024",
                    "768",
                    str(channels),
                    str(radius),
                    str(border),
                    "1",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            shape = (768, 1024) if channels == 1 else (768, 1024, channels)
            candidate = np.memmap(
                metal_output, dtype=np.float32, mode="r", shape=shape
            )
            results.append(
                {
                    "sigma": sigma,
                    "border_type": border,
                    "channels": channels,
                    "kernel_size": size,
                    "pipeline_calls": int(entry["calls"]),
                    "pipeline_opencv_seconds": float(entry["total_seconds"]),
                    "metal_full_frame_gpu_seconds": float(
                        metal_timing["gpu_seconds_mean"]
                    ),
                    "metal_full_frame_wall_seconds": float(
                        metal_timing["wall_seconds_mean"]
                    ),
                    "projected_metal_seconds_for_calls": float(
                        metal_timing["gpu_seconds_mean"]
                    )
                    * int(entry["calls"]),
                    "projected_metal_wall_seconds_for_calls": float(
                        metal_timing["wall_seconds_mean"]
                    )
                    * int(entry["calls"]),
                    "crop_opencv_seconds": crop_cpu_seconds,
                    "crop_parity": compare(reference, candidate),
                }
            )
            del candidate

    result = {
        "source_shape": list(source.shape),
        "selected_signatures": len(results),
        "covered_opencv_seconds": sum(
            item["pipeline_opencv_seconds"] for item in results
        ),
        "projected_metal_gpu_seconds": sum(
            item["projected_metal_seconds_for_calls"] for item in results
        ),
        "projected_metal_wall_seconds": sum(
            item["projected_metal_wall_seconds_for_calls"] for item in results
        ),
        "results": results,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
