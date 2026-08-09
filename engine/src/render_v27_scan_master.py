#!/usr/bin/env python3
"""Render one native-resolution V27 Blu-ray scan master from ProRes RAW."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v27_profile
from render_v23_dual_masters import save_still, sha256, summarize


def hardlink_or_copy(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    try:
        os.link(source, destination)
        return "hardlink"
    except OSError:
        import shutil

        shutil.copy2(source, destination)
        return "copy"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--reuse-v26-projection", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument("--oversample", type=int, default=1)
    parser.add_argument("--opencv-threads", type=int, default=8)
    parser.add_argument("--binomial-workers", type=int, default=8)
    parser.add_argument("--numba-threads", type=int, default=12)
    parser.add_argument(
        "--array-workers",
        type=int,
        default=0,
        help="row-parallel exact array workers; 0 selects the M4 Max optimum",
    )
    parser.add_argument("--accelerated-cpu-exact", action="store_true")
    parser.add_argument("--production-float32-spatial", action="store_true")
    parser.add_argument(
        "--production-residual-convolution",
        action="store_true",
        help=(
            "experimental Production-only L(sample-expectation) dye-cloud "
            "filter reassociation; never Archive exact"
        ),
    )
    parser.add_argument("--metal-gaussian-production", action="store_true")
    args = parser.parse_args()
    effective_array_workers = (
        args.array_workers
        if args.array_workers > 0
        else min(max(args.numba_threads, 1), 12)
    )

    v27_profile.apply(e)
    cv2.setNumThreads(args.opencv_threads)
    e.BINOMIAL_PARALLEL_WORKERS = args.binomial_workers
    if args.accelerated_cpu_exact:
        import v27_accel

        v27_accel.apply(
            e,
            numba_threads=args.numba_threads,
            array_workers=effective_array_workers,
            exact_only=True,
        )
        v27_accel.warm(e)
    production_float32_enabled = (
        args.production_float32_spatial
        or args.production_residual_convolution
        or args.metal_gaussian_production
    )
    if production_float32_enabled:
        if not args.accelerated_cpu_exact:
            raise ValueError("float32 production mode requires accelerated CPU mode")
        import v27_production_accel

        v27_production_accel.apply(
            e,
            residual_convolution=args.production_residual_convolution,
        )
    metal_bridge = None
    if args.metal_gaussian_production:
        import metal_gaussian_bridge

        metal_gaussian_bridge.install()
        metal_bridge = metal_gaussian_bridge
    total_start = time.perf_counter()
    width, height, fps = e.probe_video(args.input)
    scan_dir = args.output / "bluray_scan"
    projection_dir = args.output / "projection"
    scan_dir.mkdir(parents=True, exist_ok=True)
    projection_dir.mkdir(parents=True, exist_ok=True)
    scan_path = scan_dir / "05_emulsion_master_prores4444.mov"
    encoder = subprocess.Popen(
        e.prores_encoder_command(scan_path, width, height, fps),
        stdin=subprocess.PIPE,
    )
    decoder = subprocess.Popen(
        [str(args.decoder), str(args.input), str(args.start_frame), str(args.frames)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert decoder.stdout is not None
    frame_bytes = width * height * 3 * 4
    representative_index = args.frames // 2
    representative: np.ndarray | None = None
    stages: dict[str, list[float]] = {
        "decode_read": [],
        "scene_and_mean_negative": [],
        "stochastic_emulsion": [],
        "scan_render": [],
        "encode_write": [],
    }
    processed = 0
    while processed < args.frames:
        mark = time.perf_counter()
        payload = decoder.stdout.read(frame_bytes)
        stages["decode_read"].append(time.perf_counter() - mark)
        if len(payload) != frame_bytes:
            break
        raw = np.frombuffer(payload, dtype="<f4").reshape(height, width, 3)

        mark = time.perf_counter()
        film = e.scene_to_5279_film_rgb(
            raw,
            exposure_stops=args.exposure_stops,
            raw_colour="panasonic_official",
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.film_records_from_rgb(film)
        mean_density = e.develop_5279_record_density(records)
        stages["scene_and_mean_negative"].append(time.perf_counter() - mark)

        frame_number = args.start_frame + processed
        mark = time.perf_counter()
        formed_density = e.form_5279_multilayer_record_density(
            records,
            frame_number,
            args.grain_scale,
            args.oversample,
            precomputed_mean_density=(mean_density if args.oversample == 1 else None),
        )
        stages["stochastic_emulsion"].append(time.perf_counter() - mark)

        mark = time.perf_counter()
        scan = e.reconstruct_density_pair_to_display(
            mean_density,
            formed_density,
            frame_number,
            args.grain_scale,
            "cineon_bluray",
            "legacy_bt709_oetf",
        )
        stages["scan_render"].append(time.perf_counter() - mark)

        mark = time.perf_counter()
        encoded = np.rint(np.clip(scan, 0.0, 1.0) * 65535.0).astype("<u2")
        assert encoder.stdin is not None
        encoder.stdin.write(encoded.tobytes())
        stages["encode_write"].append(time.perf_counter() - mark)
        if processed == representative_index:
            representative = scan.copy()
        processed += 1
        elapsed = time.perf_counter() - total_start
        eta = elapsed / processed * (args.frames - processed)
        print(
            f"V27 scan frame {processed}/{args.frames} · elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
            flush=True,
        )

    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError("ProRes RAW decoder failed")
    if processed != args.frames:
        raise RuntimeError(f"decoded {processed} frames; expected {args.frames}")
    assert encoder.stdin is not None
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError("scan encoder failed")
    e.finalize_prores_rec709_metadata(scan_path)
    if representative is None:
        raise RuntimeError("missing representative frame")
    save_still(scan_dir / "still_emulsion.jpg", representative, "scan")

    v26_projection = args.reuse_v26_projection
    projection_master = v26_projection / "05_emulsion_master_prores4444.mov"
    projection_still = v26_projection / "still_emulsion.jpg"
    reuse_method = hardlink_or_copy(
        projection_master,
        projection_dir / projection_master.name,
    )
    hardlink_or_copy(projection_still, projection_dir / projection_still.name)

    source_duration = processed / (24000.0 / 1001.0)
    total_seconds = time.perf_counter() - total_start
    timing = {
        "clock": "time.perf_counter monotonic wall clock",
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "opencv_threads": args.opencv_threads,
            "binomial_parallel_workers": e.BINOMIAL_PARALLEL_WORKERS,
            "binomial_random_stripes": e.BINOMIAL_RANDOM_STRIPES,
            "numba_threads": args.numba_threads,
            "array_workers": effective_array_workers,
            "accelerated_cpu_exact": args.accelerated_cpu_exact,
            "metal_gaussian_production": args.metal_gaussian_production,
            "production_float32_spatial": production_float32_enabled,
            "production_residual_convolution": (
                args.production_residual_convolution
            ),
        },
        "stage_summaries": {
            name: summarize(values) for name, values in stages.items()
        },
        "render_and_finalize_wall_seconds_before_hashes": total_seconds,
        "total_wall_minutes": total_seconds / 60.0,
        "rendered_source_seconds": source_duration,
        "wall_seconds_per_output_second": total_seconds / source_duration,
        "shared_frames_per_wall_second": processed / total_seconds,
        "projection_reuse": {
            "method": reuse_method,
            "reason": "V27 projection is mathematically and numerically identical to V26",
            "source": str(projection_master),
        },
    }
    (args.output / "timing.json").write_text(
        json.dumps(timing, indent=2) + "\n", encoding="utf-8"
    )

    input_hash = sha256(args.input)
    common = {
        "release": v27_profile.PROFILE["name"],
        "profile": "v27",
        "input": str(args.input),
        "input_sha256": input_hash,
        "input_dimensions": [width, height],
        "fps": fps,
        "start_frame": args.start_frame,
        "frames_processed": processed,
        "duration_seconds": source_duration,
        "input_decode": "Apple extended-linear BT.2020 RGB float32",
        "source_metadata": {
            "camera": "Panasonic DC-GH7",
            "iso": 500,
            "white_balance_kelvin": 5500,
            "shutter_angle_degrees": 180.0,
        },
        "raw_colour_transform": "Panasonic official GH7-compatible ProRes RAW camera LUT",
        "exposure_stops": args.exposure_stops,
        "grain_scale": args.grain_scale,
        "oversample": args.oversample,
        "acceleration": {
            "enabled": args.accelerated_cpu_exact,
            "mode": (
                "production float32 spatial + Metal Gaussian + fused CPU"
                if args.metal_gaussian_production
                else "production float32 spatial + fused CPU"
                if production_float32_enabled
                else "bit-exact fused CPU kernels"
                if args.accelerated_cpu_exact
                else "reference"
            ),
            "opencv_threads": args.opencv_threads,
            "binomial_workers": args.binomial_workers,
            "numba_threads": args.numba_threads,
            "metal_gaussian_stats": (
                dict(metal_bridge.STATS) if metal_bridge is not None else None
            ),
            "parity_policy": (
                "production numerical parity; Archive exact remains CPU"
                if args.metal_gaussian_production
                else "experimental Production residual-convolution parity; Archive exact remains unchanged"
                if args.production_residual_convolution
                else "production float32 parity; maximum observed difference one 12-bit code"
                if production_float32_enabled
                else "decoded pixels bit-exact to V27 reference"
            ),
        },
        "shared_emulsion_realization": True,
        "output_pipeline": {
            "projection": "V26-identical Rec.709-D65 monitor rendering of 48-nit gamma-2.6 cinema observer / Rec.709 OETF / 1-1-1 / 12-bit ProRes 4444",
            "scan": "V27 neutral-scale-constrained Rec.709-D65 Blu-ray rendering / Rec.709 OETF / 1-1-1 / 12-bit ProRes 4444; BT.1886 reference display",
            "web": "decode Rec.709 OETF, then encode sRGB IEC 61966-2-1",
            "black_gamma_luma_policy": "V26 finished scan luminance preserved per pixel; no lift, crush or gamma change",
        },
        "v27_scan_calibration": {
            "enabled": True,
            "samples": e.SPIRIT_NEUTRAL_SCALE_CALIBRATION_SAMPLES,
            "maximum_scene_linear": e.SPIRIT_NEUTRAL_SCALE_CALIBRATION_MAX_SCENE_LINEAR,
            "method": "density-dependent RGB balance measured from the current neutral negative scale",
            "luminance_constraint": "exact per-pixel Rec.709 Y preservation before OETF",
            "period_2k_aperture": "V26 unchanged",
        },
        "hourly_research_boundary": v27_profile.PROFILE[
            "hourly_research_boundary"
        ],
        "grain_morphology": {
            "model": "V26 exposure-conditioned five-class dye-cloud spectrum unchanged",
            "fractions_by_population": e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION.tolist(),
            "amplitude_constraint": "Kodak 5279 per-record diffuse RMS at 48 micrometre aperture",
            "evidence_limit": "no published 5279 frequency-resolved NPS recovered",
        },
        "algorithm_sha256": sha256(Path(e.__file__)),
        "profile_sha256": sha256(Path(v27_profile.__file__)),
        "timing": timing,
    }
    scan_manifest = {
        **common,
        "viewing_look": "cineon_bluray",
        "output_encoding": "Rec.709 OETF / 1-1-1; BT.1886 reference display",
        "master_sha256": sha256(scan_path),
    }
    projection_manifest = {
        **common,
        "viewing_look": "2383_projection_monitor",
        "output_encoding": "Rec.709 OETF / 1-1-1",
        "master_sha256": sha256(projection_dir / projection_master.name),
        "reused_bit_exact_from_v26": True,
    }
    (scan_dir / "manifest.json").write_text(
        json.dumps(scan_manifest, indent=2) + "\n", encoding="utf-8"
    )
    (projection_dir / "manifest.json").write_text(
        json.dumps(projection_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(timing, indent=2), flush=True)


if __name__ == "__main__":
    main()
