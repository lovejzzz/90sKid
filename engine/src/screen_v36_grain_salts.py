#!/usr/bin/env python3
"""Render scan-only V36 salt candidates while sharing RAW/mean-negative work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

import cv2
import numpy as np

import emulsion_experiment as e
import metal_binomial_bridge
import v27_accel
import v27_production_accel
import v35_accel
import v35_profile
import render_v28_dual_masters as renderer
from render_v35_dual_masters import PRINT_LUT, PRINT_LUT_SHA256


def parse_salts(value: str) -> list[int]:
    salts = [int(item.strip(), 0) for item in value.split(",") if item.strip()]
    if not salts or len(set(salts)) != len(salts):
        raise argparse.ArgumentTypeError("salts must be a non-empty unique list")
    if any(salt < 0 or salt > 0xFFFFFFFF for salt in salts):
        raise argparse.ArgumentTypeError("every salt must fit uint32")
    return salts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument(
        "--salts",
        type=parse_salts,
        default=parse_salts("0,1,0x243f6a88,0x9e3779b9"),
    )
    parser.add_argument("--opencv-threads", type=int, default=4)
    parser.add_argument("--numba-threads", type=int, default=12)
    parser.add_argument("--array-workers", type=int, default=12)
    parser.add_argument(
        "--archive-spatial",
        action="store_true",
        help="retain the Archive optical-scatter and scan-grain kernels",
    )
    parser.add_argument(
        "--archive-sampler",
        action="store_true",
        help="retain the V34 striped-PCG64 finite-site sampler",
    )
    args = parser.parse_args()
    if args.frames < 2:
        raise ValueError("salt screening requires at least two frames")

    v35_profile.apply(e)
    cv2.setNumThreads(args.opencv_threads)
    renderer.EXPECTED_PRINT_LUT_SHA256 = PRINT_LUT_SHA256
    e._PRINT_2383_MONITOR_OUTPUT_LUT = renderer.load_validated_print_lut(PRINT_LUT)
    v27_accel.apply(
        e,
        numba_threads=args.numba_threads,
        array_workers=args.array_workers,
        exact_only=True,
    )
    v27_accel.warm(e)
    if not args.archive_spatial:
        v27_production_accel.apply(e)
    if not args.archive_sampler:
        v35_accel.warm_metal_binomial("bernoulli")

    width, height, fps = e.probe_video(args.input)
    paths = {
        salt: args.output / f"salt_{salt:08x}" / "bluray_scan"
        / "05_emulsion_master_prores4444.mov"
        for salt in args.salts
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    encoders = {
        salt: subprocess.Popen(
            e.prores_encoder_command(path, width, height, fps),
            stdin=subprocess.PIPE,
        )
        for salt, path in paths.items()
    }
    decoder = subprocess.Popen(
        [str(args.decoder), str(args.input), str(args.start_frame), str(args.frames)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert decoder.stdout is not None
    frame_bytes = width * height * 3 * 4
    timings = {f"{salt:08x}": [] for salt in args.salts}
    shared_timings = []
    total_started = time.perf_counter()

    for processed in range(args.frames):
        payload = decoder.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            raise RuntimeError(f"decoded {processed} frames; expected {args.frames}")
        raw = np.frombuffer(payload, dtype="<f4").reshape(height, width, 3)
        shared_started = time.perf_counter()
        film = e.scene_to_5279_film_rgb(
            raw,
            exposure_stops=0.45,
            raw_colour=v35_profile.PROFILE["raw_colour"],
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.film_records_from_rgb(film)
        mean_density = e.develop_5279_record_density(records)
        shared_timings.append(time.perf_counter() - shared_started)
        frame_number = args.start_frame + processed

        for salt in args.salts:
            candidate_started = time.perf_counter()
            if not args.archive_sampler:
                v35_accel.apply_metal_binomial(
                    e,
                    mode="bernoulli",
                    asynchronous=True,
                    domain_salt=salt,
                )
            formed_density = e.form_5279_multilayer_record_density(
                records,
                frame_number,
                grain_scale=1.0,
                oversample=1,
                precomputed_mean_density=mean_density,
            )
            scan = e.reconstruct_density_pair_to_display(
                mean_density,
                formed_density,
                frame_number,
                1.0,
                "cineon_bluray",
                "linear_rec709",
            )
            scan = e.bt709_encode(scan).astype(np.float32)
            encoded = np.rint(np.clip(scan, 0.0, 1.0) * 65535.0).astype("<u2")
            encoder = encoders[salt]
            assert encoder.stdin is not None
            encoder.stdin.write(encoded.tobytes())
            timings[f"{salt:08x}"].append(time.perf_counter() - candidate_started)
            del formed_density, scan, encoded
        del raw, film, records, mean_density
        elapsed = time.perf_counter() - total_started
        eta = elapsed / (processed + 1) * (args.frames - processed - 1)
        print(
            f"V36 salt screen {processed + 1}/{args.frames} · "
            f"elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
            flush=True,
        )

    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError("ProRes RAW decoder failed")
    for salt, encoder in encoders.items():
        assert encoder.stdin is not None
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f"salt {salt:08x} encoder failed")
        e.finalize_prores_rec709_metadata(paths[salt])

    report = {
        "input": str(args.input),
        "start_frame": args.start_frame,
        "frames": args.frames,
        "salts_uint32": args.salts,
        "salt_policy": "one global salt; never selected per shot",
        "sampler": "V34 striped PCG64" if args.archive_sampler else "Philox-u32",
        "spatial_kernels": "Archive" if args.archive_spatial else "Production float32",
        "shared_mean_seconds_per_frame": float(np.mean(shared_timings)),
        "candidate_seconds_per_frame": {
            key: float(np.mean(values)) for key, values in timings.items()
        },
        "total_wall_seconds": time.perf_counter() - total_started,
        "metal_stats": dict(metal_binomial_bridge.STATS),
        "outputs": {f"{salt:08x}": str(path) for salt, path in paths.items()},
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "salt_screen_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
