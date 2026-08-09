#!/usr/bin/env python3
"""Benchmark V34-equivalent V35 pipeline candidates on one native frame.

This is a research harness, not a release renderer. It forms the shared 5279
negative, both complete observers and the integrated V31 colour boundary, then
compares 16-bit signal codes against an archived CPU reference.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import cProfile
import hashlib
import json
import pstats
import resource
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from apply_v31_normal_process_adapter import adapt_frame_linear
import render_v28_dual_masters as dual_renderer
from render_v34_dual_masters import V34_PRINT_LUT_SHA256
import v34_profile


PRINT_LUT = (
    Path(__file__).resolve().parents[1]
    / "cache/print_2383_monitor_output_lut_193_v30.npy"
)


def decode_frame(source: Path, decoder: Path, index: int, cache: Path) -> np.ndarray:
    width, height, _ = e.probe_video(source)
    if cache.exists():
        raw = np.load(cache, mmap_mode="r")
        if raw.shape != (height, width, 3) or raw.dtype != np.float32:
            raise ValueError(f"invalid cached frame: {cache}")
        return np.asarray(raw)
    process = subprocess.run(
        [str(decoder), str(source), str(index), "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    raw = np.frombuffer(process.stdout, dtype="<f4")
    expected = width * height * 3
    if raw.size != expected:
        raise RuntimeError(f"decoded {raw.size} floats; expected {expected}")
    raw = raw.reshape(height, width, 3)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, raw)
    return raw


def timed(stages: dict[str, float], name: str, function, *args, **kwargs):
    started = time.perf_counter()
    result = function(*args, **kwargs)
    stages[name] = time.perf_counter() - started
    return result


def signal_codes(linear: np.ndarray) -> np.ndarray:
    signal = e.bt709_encode(linear)
    return np.rint(np.clip(signal, 0.0, 1.0) * 65535.0).astype("<u2")


def compare_codes(candidate: np.ndarray, reference_path: Path) -> dict[str, object]:
    reference = np.load(reference_path, mmap_mode="r")
    if reference.shape != candidate.shape or reference.dtype != candidate.dtype:
        raise ValueError(f"reference mismatch: {reference_path}")
    delta = candidate.astype(np.int32) - reference.astype(np.int32)
    absolute = np.abs(delta)
    return {
        "identical": bool(np.array_equal(candidate, reference)),
        "maximum_code_delta_16bit": int(absolute.max()),
        "mean_absolute_code_delta_16bit": float(absolute.mean()),
        "p99_9_absolute_code_delta_16bit": float(np.percentile(absolute, 99.9)),
        "fraction_changed": float(np.mean(absolute != 0)),
        "fraction_above_eight_16bit_codes": float(np.mean(absolute > 8)),
    }


def render(
    raw: np.ndarray,
    frame_index: int,
    metal_post=None,
    observer_workers: int = 1,
    v35_adapter: bool = False,
    metal_adapter_blur: bool = False,
    metal_mean=None,
) -> tuple[dict[str, np.ndarray], dict[str, float], dict[str, np.ndarray]]:
    stages: dict[str, float] = {}
    film = timed(
        stages,
        "scene_to_film",
        e.scene_to_5279_film_rgb,
        raw,
        0.45,
        v34_profile.PROFILE["raw_colour"],
        True,
        "photochemical",
    )
    records = timed(stages, "film_records", e.film_records_from_rgb, film)
    if metal_mean is not None:
        metal_mean.install()
    try:
        mean_density = timed(
            stages, "mean_negative", e.develop_5279_record_density, records
        )
    finally:
        if metal_mean is not None:
            metal_mean.uninstall()
    formed_density = timed(
        stages,
        "stochastic_emulsion",
        e.form_5279_multilayer_record_density,
        records,
        frame_index,
        1.0,
        1,
        mean_density,
    )
    if metal_post is not None:
        metal_post.install()
    if observer_workers == 2:
        started = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            projection_future = pool.submit(
                e.reconstruct_density_pair_to_display,
                mean_density,
                formed_density,
                frame_index,
                1.0,
                "2383_projection_monitor",
                "linear_rec709",
            )
            scan_future = pool.submit(
                e.reconstruct_density_pair_to_display,
                mean_density,
                formed_density,
                frame_index,
                1.0,
                "cineon_bluray",
                "linear_rec709",
            )
            projection = projection_future.result()
            scan = scan_future.result()
        stages["observers_parallel"] = time.perf_counter() - started
    else:
        projection = timed(
            stages,
            "projection_observer",
            e.reconstruct_density_pair_to_display,
            mean_density,
            formed_density,
            frame_index,
            1.0,
            "2383_projection_monitor",
            "linear_rec709",
        )
        scan = timed(
            stages,
            "scan_observer",
            e.reconstruct_density_pair_to_display,
            mean_density,
            formed_density,
            frame_index,
            1.0,
            "cineon_bluray",
            "linear_rec709",
        )
    if v35_adapter:
        import v31_profile
        import v35_accel

        projection = timed(
            stages,
            "final_projection_adapter",
            v35_accel.adapt_frame_linear_memory_reuse,
            e,
            projection,
            scan,
            v31_profile.PROFILE["projection_chroma_crossover_sigma_at_2k"],
            metal_adapter_blur,
        )
    else:
        projection = timed(
            stages, "final_projection_adapter", adapt_frame_linear, projection, scan
        )
    outputs = {
        "projection": signal_codes(projection),
        "scan": signal_codes(scan),
    }
    densities = {"mean_density": mean_density, "formed_density": formed_density}
    return outputs, stages, densities


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--frame-index", type=int, default=0)
    parser.add_argument("--opencv-threads", type=int, default=12)
    parser.add_argument("--array-workers", type=int, default=12)
    parser.add_argument("--observer-workers", type=int, choices=(1, 2), default=1)
    parser.add_argument("--accelerated-cpu-exact", action="store_true")
    parser.add_argument("--metal-gaussian", action="store_true")
    parser.add_argument("--metal-gaussian-post-formation", action="store_true")
    parser.add_argument("--metal-gaussian-mean-only", action="store_true")
    parser.add_argument(
        "--metal-binomial", choices=("inverse", "bernoulli")
    )
    parser.add_argument("--metal-binomial-async", action="store_true")
    parser.add_argument("--residual-convolution", action="store_true")
    parser.add_argument("--single-gaussian-after-disk", action="store_true")
    parser.add_argument("--production-float32-spatial", action="store_true")
    parser.add_argument("--v35-adapter-memory-reuse", action="store_true")
    parser.add_argument("--metal-adapter-blur", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--save-density", action="store_true")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    v34_profile.apply(e)
    cv2.setNumThreads(args.opencv_threads)
    e.BINOMIAL_PARALLEL_WORKERS = args.array_workers
    dual_renderer.EXPECTED_PRINT_LUT_SHA256 = V34_PRINT_LUT_SHA256
    e._PRINT_2383_MONITOR_OUTPUT_LUT = dual_renderer.load_validated_print_lut(
        PRINT_LUT
    )
    if args.accelerated_cpu_exact:
        import v27_accel

        v27_accel.apply(
            e,
            numba_threads=min(args.array_workers, 12),
            array_workers=args.array_workers,
            exact_only=True,
        )
        v27_accel.warm(e)
    if args.production_float32_spatial:
        import v27_production_accel

        v27_production_accel.apply(e)
    metal_binomial = None
    if args.metal_binomial:
        import metal_binomial_bridge as metal_binomial
        import v35_accel

        for key in metal_binomial.STATS:
            metal_binomial.STATS[key] = 0 if key == "calls" else 0.0
        v35_accel.apply_metal_binomial(
            e,
            mode=args.metal_binomial,
            asynchronous=args.metal_binomial_async,
            residual_convolution=args.residual_convolution,
            single_gaussian_after_disk=args.single_gaussian_after_disk,
        )
        v35_accel.warm_metal_binomial(args.metal_binomial)
    metal = None
    if (
        args.metal_gaussian
        or args.metal_gaussian_post_formation
        or args.metal_gaussian_mean_only
    ):
        import metal_gaussian_bridge as metal

        for key in metal.STATS:
            metal.STATS[key] = 0 if key.endswith("calls") else 0.0
        if args.metal_gaussian:
            metal.install()
    if args.metal_adapter_blur:
        import metal_gaussian_bridge

        warm = metal_gaussian_bridge.aligned_empty((64, 64, 2))
        warm.fill(0.5)
        metal_gaussian_bridge.submit_gaussian_async(warm, 2.0).wait()

    raw = decode_frame(args.source, args.decoder, args.frame_index, args.cache)
    profiler = cProfile.Profile()
    started = time.perf_counter()
    if args.profile:
        profiler.enable()
    outputs, stages, densities = render(
        raw,
        args.frame_index,
        metal if args.metal_gaussian_post_formation else None,
        args.observer_workers,
        args.v35_adapter_memory_reuse,
        args.metal_adapter_blur,
        metal if args.metal_gaussian_mean_only else None,
    )
    if args.profile:
        profiler.disable()
    wall = time.perf_counter() - started

    comparisons: dict[str, object] = {}
    for name, codes in outputs.items():
        np.save(args.output / f"{name}_u16.npy", codes)
        if args.reference:
            comparisons[name] = compare_codes(
                codes, args.reference / f"{name}_u16.npy"
            )
    if args.save_density:
        for name, density in densities.items():
            np.save(args.output / f"{name}.npy", density)
    if args.profile:
        profiler.dump_stats(args.output / "profile.prof")
        with (args.output / "profile_top.txt").open("w", encoding="utf-8") as stream:
            pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(120)

    report = {
        "candidate": {
            "accelerated_cpu_exact": args.accelerated_cpu_exact,
            "metal_gaussian": args.metal_gaussian,
            "metal_gaussian_post_formation": args.metal_gaussian_post_formation,
            "metal_gaussian_mean_only": args.metal_gaussian_mean_only,
            "metal_binomial": args.metal_binomial,
            "metal_binomial_async": args.metal_binomial_async,
            "residual_convolution": args.residual_convolution,
            "single_gaussian_after_disk": args.single_gaussian_after_disk,
            "production_float32_spatial": args.production_float32_spatial,
            "observer_workers": args.observer_workers,
            "v35_adapter_memory_reuse": args.v35_adapter_memory_reuse,
            "metal_adapter_blur": args.metal_adapter_blur,
        },
        "source": str(args.source),
        "frame_index": args.frame_index,
        "shape": list(outputs["projection"].shape),
        "wall_seconds": wall,
        "stage_seconds": stages,
        "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**3,
        "sha256": {
            name: hashlib.sha256(codes.tobytes()).hexdigest()
            for name, codes in outputs.items()
        },
        "comparisons": comparisons,
        "metal_gaussian_stats": dict(metal.STATS) if metal else None,
        "metal_binomial_stats": (
            dict(metal_binomial.STATS) if metal_binomial else None
        ),
        "sampler_identity_audit": (
            v35_accel.sampler_audit_snapshot() if args.metal_binomial else None
        ),
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
