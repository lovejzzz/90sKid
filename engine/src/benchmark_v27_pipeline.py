#!/usr/bin/env python3
"""Profile one native V27 frame without changing the release renderer."""

from __future__ import annotations

import argparse
import cProfile
import json
import pstats
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v27_profile


def decode_frame(
    source: Path,
    decoder: Path,
    frame_index: int,
    cache: Path,
) -> np.ndarray:
    width, height, _ = e.probe_video(source)
    expected = width * height * 3
    if cache.exists():
        raw = np.load(cache, mmap_mode="r")
        if raw.shape != (height, width, 3) or raw.dtype != np.float32:
            raise ValueError(f"invalid cached frame: {cache}")
        return np.asarray(raw)
    cache.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        [str(decoder), str(source), str(frame_index), "1"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    raw = np.frombuffer(process.stdout, dtype="<f4")
    if raw.size != expected:
        raise RuntimeError(f"decoded {raw.size} floats; expected {expected}")
    raw = raw.reshape(height, width, 3)
    np.save(cache, raw)
    return raw


def timed(name: str, timings: dict[str, float], function, *args, **kwargs):
    started = time.perf_counter()
    result = function(*args, **kwargs)
    timings[name] = time.perf_counter() - started
    return result


def render_frame(raw: np.ndarray, frame_index: int) -> tuple[np.ndarray, dict[str, float]]:
    timings: dict[str, float] = {}
    film = timed(
        "scene_to_film",
        timings,
        e.scene_to_5279_film_rgb,
        raw,
        0.45,
        "panasonic_official",
        True,
        "photochemical",
    )
    records = timed("film_records", timings, e.film_records_from_rgb, film)
    mean_density = timed(
        "mean_negative", timings, e.develop_5279_record_density, records
    )
    formed_density = timed(
        "stochastic_emulsion",
        timings,
        e.form_5279_multilayer_record_density,
        records,
        frame_index,
        1.0,
        1,
        mean_density,
    )
    scan = timed(
        "scan_render",
        timings,
        e.reconstruct_density_pair_to_display,
        mean_density,
        formed_density,
        frame_index,
        1.0,
        "cineon_bluray",
        "legacy_bt709_oetf",
    )
    return scan, timings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--opencv-threads", type=int, default=8)
    parser.add_argument("--binomial-workers", type=int, default=8)
    parser.add_argument("--array-workers", type=int, default=1)
    parser.add_argument("--accel", action="store_true")
    parser.add_argument("--accel-exact-only", action="store_true")
    parser.add_argument("--accel-record-only", action="store_true")
    parser.add_argument("--accel-record-semi", action="store_true")
    parser.add_argument("--accel-matrix-only", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--trace-gaussian", action="store_true")
    parser.add_argument("--metal-gaussian", action="store_true")
    parser.add_argument("--production-float32-spatial", action="store_true")
    parser.add_argument("--production-residual-convolution", action="store_true")
    parser.add_argument("--profile-stochastic-operators", action="store_true")
    parser.add_argument("--profile-mean-operators", action="store_true")
    args = parser.parse_args()

    v27_profile.apply(e)
    if args.profile_stochastic_operators:
        e._V27_STOCHASTIC_PROFILE = {}
    if args.profile_mean_operators:
        e._V27_MEAN_PROFILE = {}
    cv2.setNumThreads(args.opencv_threads)
    e.BINOMIAL_PARALLEL_WORKERS = args.binomial_workers
    acceleration_requested = any(
        (
            args.accel,
            args.accel_exact_only,
            args.accel_record_only,
            args.accel_record_semi,
            args.accel_matrix_only,
        )
    )
    if acceleration_requested:
        import v27_accel

        v27_accel.apply(
            e,
            numba_threads=min(args.binomial_workers, 12),
            array_workers=args.array_workers,
            exact_only=args.accel_exact_only,
            enable_record_density=(
                "semi" if args.accel_record_semi else not args.accel_matrix_only
            ),
            enable_matrix=not (args.accel_record_only or args.accel_record_semi),
        )
    if args.production_float32_spatial or args.production_residual_convolution:
        import v27_production_accel

        v27_production_accel.apply(
            e,
            residual_convolution=args.production_residual_convolution,
        )
    metal_bridge = None
    if args.metal_gaussian:
        import metal_gaussian_bridge

        metal_gaussian_bridge.install()
        metal_bridge = metal_gaussian_bridge
    gaussian_trace: dict[tuple[object, ...], dict[str, object]] = {}
    if args.trace_gaussian:
        reference_gaussian = cv2.GaussianBlur

        def traced_gaussian(source, ksize, sigma_x, *positional, **keywords):
            sigma_y = (
                positional[0]
                if positional
                else keywords.get("sigmaY", 0.0)
            )
            border = keywords.get(
                "borderType",
                positional[1] if len(positional) > 1 else cv2.BORDER_DEFAULT,
            )
            shape = tuple(int(value) for value in np.asarray(source).shape)
            key = (
                shape,
                tuple(int(value) for value in ksize),
                float(sigma_x),
                float(sigma_y),
                int(border),
            )
            started = time.perf_counter()
            result = reference_gaussian(
                source, ksize, sigma_x, *positional, **keywords
            )
            seconds = time.perf_counter() - started
            entry = gaussian_trace.setdefault(
                key,
                {
                    "shape": list(shape),
                    "ksize": list(ksize),
                    "sigma_x": float(sigma_x),
                    "sigma_y": float(sigma_y),
                    "border_type": int(border),
                    "calls": 0,
                    "total_seconds": 0.0,
                },
            )
            entry["calls"] = int(entry["calls"]) + 1
            entry["total_seconds"] = float(entry["total_seconds"]) + seconds
            return result

        cv2.GaussianBlur = traced_gaussian
    raw = decode_frame(args.source, args.decoder, args.frame_index, args.cache)
    args.output.mkdir(parents=True, exist_ok=True)

    profiler = cProfile.Profile()
    started = time.perf_counter()
    if args.profile:
        profiler.enable()
    scan, timings = render_frame(raw, args.frame_index)
    if args.profile:
        profiler.disable()
    wall = time.perf_counter() - started

    encoded = np.rint(np.clip(scan, 0.0, 1.0) * 65535.0).astype("<u2")
    np.save(args.output / "reference_u16.npy", encoded)
    result = {
        "shape": list(scan.shape),
        "opencv_threads": args.opencv_threads,
        "binomial_workers": args.binomial_workers,
        "array_workers": args.array_workers,
        "acceleration_enabled": acceleration_requested,
        "acceleration_exact_only": args.accel_exact_only,
        "acceleration_record_only": args.accel_record_only,
        "acceleration_record_semi": args.accel_record_semi,
        "acceleration_matrix_only": args.accel_matrix_only,
        "production_float32_spatial": args.production_float32_spatial,
        "production_residual_convolution": (
            args.production_residual_convolution
        ),
        "stage_seconds": timings,
        "wall_seconds": wall,
        "output_min": float(scan.min()),
        "output_max": float(scan.max()),
        "output_mean": [float(value) for value in scan.mean(axis=(0, 1))],
    }
    if metal_bridge is not None:
        result["metal_gaussian_stats"] = dict(metal_bridge.STATS)
    if args.profile_stochastic_operators:
        result["stochastic_operator_profile"] = {
            "measurement": (
                "summed task wall-seconds; dye-cloud calls overlap across "
                "binomial worker threads"
            ),
            "entries": e._V27_STOCHASTIC_PROFILE,
        }
    if args.profile_mean_operators:
        result["mean_operator_profile"] = {
            "measurement": "summed task wall-seconds",
            "entries": e._V27_MEAN_PROFILE,
        }
    (args.output / "baseline.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    if args.trace_gaussian:
        entries = sorted(
            gaussian_trace.values(),
            key=lambda entry: float(entry["total_seconds"]),
            reverse=True,
        )
        trace = {
            "unique_signatures": len(entries),
            "total_calls": sum(int(entry["calls"]) for entry in entries),
            "total_seconds": sum(float(entry["total_seconds"]) for entry in entries),
            "entries": entries,
        }
        (args.output / "gaussian_trace.json").write_text(
            json.dumps(trace, indent=2) + "\n", encoding="utf-8"
        )
    if args.profile:
        profiler.dump_stats(args.output / "baseline.prof")
        with (args.output / "profile_top.txt").open("w", encoding="utf-8") as handle:
            stats = pstats.Stats(profiler, stream=handle).strip_dirs().sort_stats(
                "cumulative"
            )
            stats.print_stats(100)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
