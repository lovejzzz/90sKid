#!/usr/bin/env python3
"""Render timed V23 projection-monitor and Blu-ray masters from one emulsion."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import platform
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v24_profile
import v25_profile
import v26_profile
import v27_profile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_still(path: Path, encoded: np.ndarray, branch: str) -> None:
    # Both V25 deliverables are Rec.709 monitor renderings.  BT.1886 and the
    # 48-nit / gamma-2.6 cinema observer are validation/viewing conditions, not
    # source-file OETFs.  Decode the interchange signal before making sRGB web
    # stills so the still and video always describe the same display light.
    linear = e.bt709_decode(encoded)
    display = e.srgb_encode(linear)
    image = np.rint(np.clip(display, 0.0, 1.0) * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 96])


def save_srgb_still(path: Path, encoded_srgb: np.ndarray) -> None:
    """Write an already sRGB-encoded observer image without a second transform."""
    image = np.rint(np.clip(encoded_srgb, 0.0, 1.0) * 255.0).astype(np.uint8)
    cv2.imwrite(
        str(path),
        cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
        [cv2.IMWRITE_JPEG_QUALITY, 96],
    )


def summarize(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "total_seconds": float(np.sum(array)),
        "mean_seconds_per_frame": float(np.mean(array)),
        "median_seconds_per_frame": float(np.median(array)),
        "p95_seconds_per_frame": float(np.percentile(array, 95)),
        "maximum_seconds_per_frame": float(np.max(array)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=72)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument("--oversample", type=int, default=1)
    parser.add_argument("--opencv-threads", type=int, default=8)
    parser.add_argument("--profile", choices=("v23", "v24", "v25", "v26", "v27"), default="v23")
    args = parser.parse_args()

    if args.profile == "v27":
        v27_profile.apply(e)
    elif args.profile == "v26":
        v26_profile.apply(e)
    elif args.profile == "v25":
        v25_profile.apply(e)
    elif args.profile == "v24":
        v24_profile.apply(e)
    release_name = (
        v27_profile.PROFILE["name"] if args.profile == "v27"
        else v26_profile.PROFILE["name"] if args.profile == "v26"
        else v25_profile.PROFILE["name"] if args.profile == "v25"
        else v24_profile.PROFILE["name"] if args.profile == "v24"
        else "V23 five-point dye-cloud quadrature"
    )

    cv2.setNumThreads(args.opencv_threads)

    total_start = time.perf_counter()
    width, height, fps = e.probe_video(args.input)
    projection_dir = args.output / "projection"
    scan_dir = args.output / "bluray_scan"
    projection_dir.mkdir(parents=True, exist_ok=True)
    scan_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "projection": projection_dir / "05_emulsion_master_prores4444.mov",
        "scan": scan_dir / "05_emulsion_master_prores4444.mov",
    }
    encoder_commands = {
        "projection": e.prores_encoder_command(paths["projection"], width, height, fps),
        "scan": e.prores_encoder_command(paths["scan"], width, height, fps),
    }
    encoders = {
        name: subprocess.Popen(command, stdin=subprocess.PIPE)
        for name, command in encoder_commands.items()
    }
    decoder = subprocess.Popen(
        [str(args.decoder), str(args.input), str(args.start_frame), str(args.frames)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert decoder.stdout is not None
    frame_bytes = width * height * 3 * 4
    representative_index = args.frames // 2
    representative: dict[str, np.ndarray] = {}
    stage_times: dict[str, list[float]] = {
        "decode_read": [],
        "scene_and_mean_negative": [],
        "stochastic_emulsion": [],
        "projection_render": [],
        "scan_render": [],
        "observer_render_parallel": [],
        "encode_write_both": [],
    }
    processed = 0
    while processed < args.frames:
        mark = time.perf_counter()
        payload = decoder.stdout.read(frame_bytes)
        stage_times["decode_read"].append(time.perf_counter() - mark)
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
        stage_times["scene_and_mean_negative"].append(time.perf_counter() - mark)

        frame_number = args.start_frame + processed
        mark = time.perf_counter()
        formed_density = e.form_5279_multilayer_record_density(
            records,
            frame_number,
            args.grain_scale,
            args.oversample,
            precomputed_mean_density=(
                mean_density if args.profile in ("v25", "v26", "v27") and args.oversample == 1 else None
            ),
        )
        stage_times["stochastic_emulsion"].append(time.perf_counter() - mark)

        if args.profile in ("v25", "v26", "v27"):
            mark = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as observer_pool:
                projection_future = observer_pool.submit(
                    e.reconstruct_density_pair_to_display,
                    mean_density, formed_density, frame_number, args.grain_scale,
                    "2383_projection_monitor", "legacy_bt709_oetf",
                )
                scan_future = observer_pool.submit(
                    e.reconstruct_density_pair_to_display,
                    mean_density, formed_density, frame_number, args.grain_scale,
                    "cineon_bluray", "legacy_bt709_oetf",
                )
                projection = projection_future.result()
                scan = scan_future.result()
            observer_seconds = time.perf_counter() - mark
            # Concurrent wall time is recorded once; individual observer CPU
            # time is not meaningful while both branches overlap.
            stage_times["projection_render"].append(0.0)
            stage_times["scan_render"].append(0.0)
            stage_times["observer_render_parallel"].append(observer_seconds)
        else:
            mark = time.perf_counter()
            projection = e.reconstruct_density_pair_to_display(
                mean_density, formed_density, frame_number, args.grain_scale,
                "2383_projection_monitor", "legacy_bt709_oetf",
            )
            stage_times["projection_render"].append(time.perf_counter() - mark)

            mark = time.perf_counter()
            scan = e.reconstruct_density_pair_to_display(
                mean_density, formed_density, frame_number, args.grain_scale,
                "cineon_bluray", "legacy_bt709_oetf",
            )
            stage_times["scan_render"].append(time.perf_counter() - mark)
            stage_times["observer_render_parallel"].append(0.0)

        mark = time.perf_counter()
        for name, image in (("projection", projection), ("scan", scan)):
            encoded = np.rint(np.clip(image, 0.0, 1.0) * 65535.0).astype("<u2")
            assert encoders[name].stdin is not None
            encoders[name].stdin.write(encoded.tobytes())
        stage_times["encode_write_both"].append(time.perf_counter() - mark)

        if processed == representative_index:
            representative = {"projection": projection.copy(), "scan": scan.copy()}
        processed += 1
        elapsed = time.perf_counter() - total_start
        eta = elapsed / processed * (args.frames - processed)
        print(f"{args.profile.upper()} shared-emulsion frame {processed}/{args.frames} · elapsed {elapsed:.1f}s · ETA {eta:.1f}s", flush=True)

    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError("ProRes RAW decoder failed")
    if processed != args.frames:
        raise RuntimeError(f"decoded {processed} frames; expected {args.frames}")

    encode_finalize_start = time.perf_counter()
    for name, encoder in encoders.items():
        assert encoder.stdin is not None
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f"{name} encoder failed")
        e.finalize_prores_rec709_metadata(paths[name])
    encode_finalize_seconds = time.perf_counter() - encode_finalize_start

    for name, image in representative.items():
        directory = projection_dir if name == "projection" else scan_dir
        save_still(directory / "still_emulsion.jpg", image, name)

    hash_start = time.perf_counter()
    input_hash = sha256(args.input)
    master_hashes = {name: sha256(path) for name, path in paths.items()}
    hash_seconds = time.perf_counter() - hash_start
    total_seconds = time.perf_counter() - total_start
    source_duration = processed / (24000.0 / 1001.0)
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
        },
        "stage_summaries": {name: summarize(values) for name, values in stage_times.items()},
        "encoder_close_remux_seconds": encode_finalize_seconds,
        "sha256_seconds": hash_seconds,
        "total_wall_seconds_including_hashes": total_seconds,
        "total_wall_minutes": total_seconds / 60.0,
        "rendered_source_seconds": source_duration,
        "wall_seconds_per_output_second_for_two_masters": total_seconds / source_duration,
        "shared_frames_per_wall_second": processed / total_seconds,
        "shared_megapixels_per_wall_second": processed * width * height / 1e6 / total_seconds,
    }
    (args.output / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")

    common = {
        "release": release_name,
        "profile": args.profile,
        "input": str(args.input),
        "input_sha256": input_hash,
        "input_dimensions": [width, height],
        "fps": fps,
        "start_frame": args.start_frame,
        "frames_processed": processed,
        "duration_seconds": source_duration,
        "input_decode": "Apple extended-linear BT.2020 RGB float32",
        "source_metadata": {"camera": "Panasonic DC-GH7", "iso": 500, "white_balance_kelvin": 5500, "shutter_angle_degrees": 180.0},
        "raw_colour_transform": "Panasonic official GH7-compatible ProRes RAW camera LUT",
        "exposure_stops": args.exposure_stops,
        "grain_scale": args.grain_scale,
        "oversample": args.oversample,
        "shared_emulsion_realization": True,
        "output_pipeline": (
            {
                "projection": "Rec.709-D65 monitor rendering of 48-nit gamma-2.6 cinema observer / Rec.709 OETF / 1-1-1 / 12-bit ProRes 4444",
                "scan": "Rec.709-D65 Blu-ray rendering / Rec.709 OETF / 1-1-1 / 12-bit ProRes 4444; BT.1886 is the reference display EOTF",
                "web": "decode Rec.709 OETF, then encode sRGB IEC 61966-2-1",
                "black_policy": "no output-stage crush or lift; stock/print/scan black retained in display linear",
                "corrected_reference_pipeline": "BT.1886 and cinema gamma are observer conditions, not source-file OETFs; removed the inverse-EOTF double transform",
            }
            if args.profile in ("v25", "v26", "v27") else None
        ),
        "acceleration": (
            {
                "method": "fixed seeded row-stripe scheduling of exact binomial samples",
                "quality_shortcuts": [],
                "worker_invariance": "same fixed stripes and seeds at 1 or N workers",
            }
            if args.profile in ("v25", "v26", "v27") else None
        ),
        "grain_morphology": {
            "model": "five-point log-normal-like dye-cloud quadrature with golden-angle subpixel phases",
            "correlation_scale": e.NEGATIVE_GRAIN_CORRELATION_SCALE,
            "fractions": e.GRAIN_SIZE_CLASS_FRACTIONS.tolist(),
            "fractions_by_population": (
                None
                if e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION is None
                else e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION.tolist()
            ),
            "radius_factors": e.GRAIN_SIZE_CLASS_RADIUS_FACTORS.tolist(),
            "optical_factors": e.GRAIN_SIZE_CLASS_OPTICAL_FACTORS.tolist(),
            "phase_step_radians": e.GRAIN_SIZE_CLASS_PHASE_STEP_RADIANS,
            "amplitude_constraint": "Kodak 5279 per-record diffuse RMS at 48 micrometre aperture",
        },
        "visible_colour_grain_integration": {
            "projection_sigma_at_2k": e.PROJECTION_CHROMA_GRAIN_SIGMA_AT_2K,
            "projection_high_frequency_retention": e.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION,
            "projection_opponent_strength": e.PROJECTION_CHROMA_GRAIN_OPPONENT_STRENGTH,
            "scan_sigma_at_2k": e.BLURAY_CHROMA_GRAIN_SIGMA_AT_2K,
            "scan_high_frequency_retention": e.BLURAY_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION,
            "scan_opponent_strength": e.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH,
            "mean_colour_constraint": "signed grain delta only; deterministic mean branch unchanged",
        },
        "colour_model": "V22 analytical-dye 2383 and neutral-subtracted D60-relative monitor calibration retained after D55/D60/D65 triad candidate produced no material held-out improvement",
        "algorithm_sha256": sha256(Path(e.__file__)),
        "profile_sha256": sha256(
            Path(v27_profile.__file__)
            if args.profile == "v27"
            else Path(v26_profile.__file__)
            if args.profile == "v26"
            else Path(v25_profile.__file__)
            if args.profile == "v25"
            else Path(v24_profile.__file__)
        ),
        "timing": timing,
    }
    manifests = {
        "projection": {**common, "viewing_look": "2383_projection_monitor", "output_encoding": "Rec.709 OETF / 1-1-1", "master_sha256": master_hashes["projection"]},
        "scan": {**common, "viewing_look": "cineon_bluray", "output_encoding": "Rec.709 OETF / 1-1-1; BT.1886 reference display", "master_sha256": master_hashes["scan"]},
    }
    for name, manifest in manifests.items():
        directory = projection_dir if name == "projection" else scan_dir
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(timing, indent=2), flush=True)


if __name__ == "__main__":
    main()
