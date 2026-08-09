#!/usr/bin/env python3
"""Render native V28 projection and Blu-ray masters from one emulsion."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v28_profile
from render_v23_dual_masters import save_srgb_still, save_still, sha256, summarize


DEFAULT_PRINT_LUT_CACHE = (
    Path(__file__).resolve().parents[1]
    / "cache"
    / "print_2383_monitor_output_lut_193_v28.npy"
)
EXPECTED_PRINT_LUT_SHA256 = (
    "647ee4b66c17e6267071bf441b69df7084e8256d6c583d1d56f04719a0606bab"
)


def load_validated_print_lut(path: Path) -> np.ndarray:
    """Load the immutable analytical 2383 lattice after integrity checks."""
    if not path.exists():
        raise FileNotFoundError(f"missing validated 2383 cache: {path}")
    digest = sha256(path)
    if digest != EXPECTED_PRINT_LUT_SHA256:
        raise ValueError(
            "2383 cache hash does not match the V28 analytical lattice: "
            f"{digest}"
        )
    lattice = np.load(path, allow_pickle=False)
    if lattice.shape != (193, 193, 193, 3) or lattice.dtype != np.float32:
        raise ValueError("invalid V28 2383 output lattice")
    return lattice


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument("--oversample", type=int, default=1)
    parser.add_argument("--opencv-threads", type=int, default=16)
    parser.add_argument("--binomial-workers", type=int, default=12)
    parser.add_argument("--numba-threads", type=int, default=12)
    parser.add_argument("--array-workers", type=int, default=12)
    parser.add_argument(
        "--observer-workers",
        type=int,
        choices=(1, 2),
        default=1,
        help=(
            "Render projection and scan concurrently or sequentially. Use 1 "
            "with Numba's non-threadsafe workqueue backend."
        ),
    )
    parser.add_argument(
        "--print-lut-cache", type=Path, default=DEFAULT_PRINT_LUT_CACHE
    )
    parser.add_argument("--accelerated-cpu-exact", action="store_true")
    parser.add_argument("--v35-production-pipeline", action="store_true")
    parser.add_argument(
        "--grain-domain-salt",
        type=lambda value: int(value, 0),
        default=0,
        help="uint32 Philox domain salt; zero reproduces the V35 realization",
    )
    args = parser.parse_args()
    if args.frames < 1:
        raise ValueError("frames must be positive")

    v28_profile.apply(e)
    integrated_final_adapter = (
        v28_profile.PROFILE.get("final_projection_adapter")
        == "v31_scan_low_frequency_chroma"
    )
    dual_display_delivery = (
        v28_profile.PROFILE.get("delivery_family")
        == "display_linear_dual_encoding"
    )
    if dual_display_delivery and not integrated_final_adapter:
        raise ValueError("V38 dual delivery requires the integrated linear adapter")
    cv2.setNumThreads(args.opencv_threads)
    e.BINOMIAL_PARALLEL_WORKERS = args.binomial_workers
    if args.accelerated_cpu_exact:
        import v27_accel

        if (
            v28_profile.PROFILE.get("print_structure_domain") is None
            or v28_profile.PROFILE.get("projection_grain_delta_observer_id")
            == "archive_pointwise"
        ):
            # This lattice is the byte-for-byte output of the analytical 2383
            # builder. Loading it removes a 17.6 s per-process startup rebuild;
            # it does not replace or approximate a per-frame spatial operation.
            e._PRINT_2383_MONITOR_OUTPUT_LUT = load_validated_print_lut(
                args.print_lut_cache
            )
        v27_accel.apply(
            e,
            numba_threads=args.numba_threads,
            array_workers=args.array_workers,
            exact_only=True,
        )
        v27_accel.warm(e)
    metal_binomial = None
    if args.v35_production_pipeline:
        if not args.accelerated_cpu_exact:
            raise ValueError("V35 Production requires --accelerated-cpu-exact")
        if args.observer_workers != 1:
            raise ValueError(
                "V35 Production requires --observer-workers 1: this macOS "
                "Numba build only has the non-threadsafe workqueue backend"
            )
        import metal_binomial_bridge as metal_binomial
        import v27_production_accel
        import v35_accel

        v27_production_accel.apply(e)
        v35_accel.apply_metal_binomial(
            e,
            mode="bernoulli",
            asynchronous=True,
            domain_salt=args.grain_domain_salt,
        )
        v35_accel.warm_metal_binomial("bernoulli")

    total_start = time.perf_counter()
    width, height, fps = e.probe_video(args.input)
    output_dirs = {
        "projection": args.output / "projection",
        "scan": args.output / "bluray_scan",
    }
    for directory in output_dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    paths = {
        name: directory / "05_emulsion_master_prores4444.mov"
        for name, directory in output_dirs.items()
    }
    quicktime_paths = {
        name: directory / "06_quicktime_preview_srgb_prores4444.mov"
        for name, directory in output_dirs.items()
    } if dual_display_delivery else {}
    encoders = {
        name: subprocess.Popen(
            e.prores_encoder_command(path, width, height, fps),
            stdin=subprocess.PIPE,
        )
        for name, path in paths.items()
    }
    quicktime_encoders = {
        name: subprocess.Popen(
            e.prores_encoder_command(path, width, height, fps),
            stdin=subprocess.PIPE,
        )
        for name, path in quicktime_paths.items()
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
    stages: dict[str, list[float]] = {
        "decode_read": [],
        "scene_and_mean_negative": [],
        "stochastic_emulsion": [],
        "observer_render_parallel": [],
        "encode_write_both": [],
    }
    if integrated_final_adapter:
        stages["final_projection_adapter"] = []
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
            raw_colour=v28_profile.PROFILE["raw_colour"],
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
        observer_encoding = (
            "linear_rec709" if integrated_final_adapter else "legacy_bt709_oetf"
        )
        if (
            v28_profile.PROFILE.get("print_structure_domain") is not None
            and args.observer_workers == 1
        ):
            projection, scan = e.reconstruct_density_pair_to_dual_display_v39(
                mean_density,
                formed_density,
                frame_number,
                args.grain_scale,
                observer_encoding,
            )
        elif args.observer_workers == 2:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as observers:
                projection_future = observers.submit(
                    e.reconstruct_density_pair_to_display,
                    mean_density,
                    formed_density,
                    frame_number,
                    args.grain_scale,
                    "2383_projection_monitor",
                    observer_encoding,
                )
                scan_future = observers.submit(
                    e.reconstruct_density_pair_to_display,
                    mean_density,
                    formed_density,
                    frame_number,
                    args.grain_scale,
                    "cineon_bluray",
                    observer_encoding,
                )
                projection = projection_future.result()
                scan = scan_future.result()
        else:
            projection = e.reconstruct_density_pair_to_display(
                mean_density,
                formed_density,
                frame_number,
                args.grain_scale,
                "2383_projection_monitor",
                observer_encoding,
            )
            scan = e.reconstruct_density_pair_to_display(
                mean_density,
                formed_density,
                frame_number,
                args.grain_scale,
                "cineon_bluray",
                observer_encoding,
            )
        stages["observer_render_parallel"].append(time.perf_counter() - mark)

        # The observer outputs own their data; release the large RAW, record and
        # density arrays before the final full-frame colour operation.
        del raw, film, records, mean_density, formed_density
        if integrated_final_adapter:
            mark = time.perf_counter()
            if args.v35_production_pipeline:
                import v35_accel

                projection = v35_accel.adapt_frame_linear_memory_reuse(
                    e,
                    projection,
                    scan,
                    v28_profile.PROFILE[
                        "projection_chroma_crossover_sigma_at_2k"
                    ],
                    v28_profile.PROFILE.get(
                        "final_adapter_opponent_high_frequency_retention",
                        1.0,
                    ),
                )
            else:
                from apply_v31_normal_process_adapter import adapt_frame_linear

                projection = adapt_frame_linear(
                    projection,
                    scan,
                    v28_profile.PROFILE.get(
                        "final_adapter_opponent_high_frequency_retention",
                        1.0,
                    ),
                )
            if dual_display_delivery:
                quicktime_images = {
                    "projection": e.srgb_encode(projection).astype(np.float32),
                    "scan": e.srgb_encode(scan).astype(np.float32),
                }
                projection = e.bt1886_reference_encode(projection)
                scan = e.bt1886_reference_encode(scan)
            else:
                projection = e.bt709_encode(projection).astype(np.float32)
                scan = e.bt709_encode(scan).astype(np.float32)
            stages["final_projection_adapter"].append(
                time.perf_counter() - mark
            )

        mark = time.perf_counter()
        for name, image in (("projection", projection), ("scan", scan)):
            encoded = np.rint(np.clip(image, 0.0, 1.0) * 65535.0).astype("<u2")
            assert encoders[name].stdin is not None
            encoders[name].stdin.write(encoded.tobytes())
        if dual_display_delivery:
            for name, image in quicktime_images.items():
                encoded = np.rint(
                    np.clip(image, 0.0, 1.0) * 65535.0
                ).astype("<u2")
                assert quicktime_encoders[name].stdin is not None
                quicktime_encoders[name].stdin.write(encoded.tobytes())
        stages["encode_write_both"].append(time.perf_counter() - mark)
        if processed == representative_index:
            if dual_display_delivery:
                representative = {
                    name: image.copy() for name, image in quicktime_images.items()
                }
            else:
                representative = {
                    "projection": projection.copy(),
                    "scan": scan.copy(),
                }
        processed += 1
        elapsed = time.perf_counter() - total_start
        eta = elapsed / processed * (args.frames - processed)
        print(
            f"{v28_profile.PROFILE.get('short_name', 'V28')} shared-emulsion "
            f"frame {processed}/{args.frames} · "
            f"elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
            flush=True,
        )

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
    for name, encoder in quicktime_encoders.items():
        assert encoder.stdin is not None
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f"{name} QuickTime companion encoder failed")
        e.finalize_prores_srgb_metadata(quicktime_paths[name])
    for name, image in representative.items():
        if dual_display_delivery:
            save_srgb_still(output_dirs[name] / "still_emulsion.jpg", image)
        else:
            save_still(output_dirs[name] / "still_emulsion.jpg", image, name)

    total_seconds = time.perf_counter() - total_start
    pointwise_print_lut_used = (
        v28_profile.PROFILE.get("print_structure_domain") is None
        or v28_profile.PROFILE.get("projection_grain_delta_observer_id")
        == "archive_pointwise"
    )
    pipeline_provenance = {
        "command": [sys.executable, *sys.argv],
        "renderer_sha256": sha256(Path(__file__)),
        "algorithm_sha256": sha256(Path(e.__file__)),
        "profile_sha256": sha256(Path(v28_profile.__file__)),
        "print_lut_sha256": (
            EXPECTED_PRINT_LUT_SHA256 if pointwise_print_lut_used else None
        ),
        "print_observer_execution": (
            "hybrid: analytical observer for the deterministic spatial 2383 "
            "density mean; validated pointwise negative-density output LUT "
            "for the signed 5279 stochastic observer delta"
            if v28_profile.PROFILE.get("projection_grain_delta_observer_id")
            == "archive_pointwise"
            else (
                "validated pointwise negative-density output LUT"
                if pointwise_print_lut_used
                else "analytical observer after spatially formed 2383 density"
            )
        ),
    }
    if args.v35_production_pipeline:
        pipeline_provenance.update(
            {
                "v35_accel_sha256": sha256(Path(v35_accel.__file__)),
                "metal_bridge_python_sha256": sha256(
                    Path(metal_binomial.__file__)
                ),
                "metal_bridge_source_sha256": sha256(
                    Path(metal_binomial.SOURCE)
                ),
                "finite_site_seed_contract": (
                    "30000000 + frame*10000 + channel*1000 + "
                    "population*100 + size_class; Philox counter also uses "
                    "global pixel index, a sampler-domain tag and the uint32 "
                    f"domain salt {args.grain_domain_salt} in the high key word"
                ),
                "grain_domain_salt_uint32": args.grain_domain_salt,
                "finite_site_distribution_claim": (
                    "statistically validated Philox uint32 Bernoulli trials "
                    "against floor(float32_probability * 2^32); independent "
                    "production realization, not archive-bit-identical NumPy RNG"
                ),
            }
        )
    timing = {
        "clock": "time.perf_counter monotonic wall clock",
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "opencv_threads": args.opencv_threads,
            "binomial_workers": args.binomial_workers,
            "numba_threads": args.numba_threads,
            "array_workers": args.array_workers,
            "observer_workers": args.observer_workers,
            "validated_print_lut_cache": (
                str(args.print_lut_cache) if pointwise_print_lut_used else None
            ),
            "validated_print_lut_sha256": (
                EXPECTED_PRINT_LUT_SHA256 if pointwise_print_lut_used else None
            ),
            "v35_production_pipeline": args.v35_production_pipeline,
            "metal_binomial_stats": (
                dict(metal_binomial.STATS) if metal_binomial else None
            ),
            "sampler_identity_audit": (
                v35_accel.sampler_audit_snapshot()
                if args.v35_production_pipeline
                else None
            ),
        },
        "pipeline_provenance": pipeline_provenance,
        "stage_summaries": {
            name: summarize(values) for name, values in stages.items()
        },
        "total_wall_seconds_before_hashes": total_seconds,
        "effective_seconds_per_frame_for_two_masters": total_seconds / processed,
    }
    (args.output / "timing.json").write_text(
        json.dumps(timing, indent=2) + "\n", encoding="utf-8"
    )
    common = {
        "release": v28_profile.PROFILE["name"],
        "profile": v28_profile.PROFILE.get("version_id", "v28"),
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "input_dimensions": [width, height],
        "fps": fps,
        "start_frame": args.start_frame,
        "frames_processed": processed,
        "input_decode": v28_profile.PROFILE["input_decode"],
        "raw_colour_transform": v28_profile.PROFILE["raw_colour_transform"],
        "white_balance_contract": v28_profile.PROFILE["white_balance_contract"],
        "camera_lut_boundary": v28_profile.PROFILE["camera_lut_boundary"],
        "film_constraint": v28_profile.PROFILE["film_constraint"],
        "projection_lad_status_a_aim_rgb": v28_profile.PROFILE.get(
            "projection_lad_status_a_aim_rgb"
        ),
        "projection_vendor_lut_strength": v28_profile.PROFILE.get(
            "projection_vendor_lut_strength"
        ),
        "projection_physical_hue_weight": v28_profile.PROFILE.get(
            "projection_physical_hue_weight"
        ),
        "projection_physical_saturation_weight": v28_profile.PROFILE.get(
            "projection_physical_saturation_weight"
        ),
        "projection_chroma_adaptation": v28_profile.PROFILE.get(
            "projection_chroma_adaptation", "relative_saturation"
        ),
        "process_constraint": v28_profile.PROFILE.get("process_constraint"),
        "projection_change": v28_profile.PROFILE.get("projection_change"),
        "final_projection_adapter": v28_profile.PROFILE.get(
            "final_projection_adapter"
        ),
        "delivery_generation_count": (
            2 if dual_display_delivery else 1 if integrated_final_adapter else None
        ),
        "delivery_family": v28_profile.PROFILE.get("delivery_family"),
        "delivery_change": v28_profile.PROFILE.get("delivery_change"),
        "delivery_consistency_contract": v28_profile.PROFILE.get(
            "delivery_consistency_contract"
        ),
        "scan_constraint": v28_profile.PROFILE.get("scan_constraint"),
        "negative_structure_domain": v28_profile.PROFILE.get(
            "negative_structure_domain"
        ),
        "negative_granularity_calibration": v28_profile.PROFILE.get(
            "negative_granularity_calibration"
        ),
        "print_structure_domain": v28_profile.PROFILE.get(
            "print_structure_domain"
        ),
        "print_grain_model": v28_profile.PROFILE.get("print_grain_model"),
        "raw_record_boundary": v28_profile.PROFILE.get("raw_record_boundary"),
        "source_of_truth_fixes": v28_profile.PROFILE.get(
            "source_of_truth_fixes"
        ),
        "exposure_stops": args.exposure_stops,
        "grain_scale": args.grain_scale,
        "oversample": args.oversample,
        "shared_emulsion_realization": True,
        "acceleration": (
            (
                "V35 Production: V27 exact CPU + float32 spatial + "
                "Philox-u32/Metal finite-site sampler + reliable serial observers"
            )
            if args.v35_production_pipeline
            else "V27 Archive-exact fused CPU kernels"
            if args.accelerated_cpu_exact
            else "reference"
        ),
        "algorithm_sha256": sha256(Path(e.__file__)),
        "profile_sha256": sha256(Path(v28_profile.__file__)),
        "pipeline_provenance": pipeline_provenance,
        "timing": timing,
    }
    manifests = {
        "projection": {
            **common,
            "viewing_look": "2383_projection_monitor",
            "output_encoding": (
                v28_profile.PROFILE["reference_master_encoding"]
                if dual_display_delivery else "Rec.709 OETF / 1-1-1"
            ),
            "master_sha256": sha256(paths["projection"]),
            "quicktime_companion": (
                str(quicktime_paths["projection"])
                if dual_display_delivery else None
            ),
            "quicktime_companion_sha256": (
                sha256(quicktime_paths["projection"])
                if dual_display_delivery else None
            ),
        },
        "scan": {
            **common,
            "viewing_look": "cineon_bluray",
            "output_encoding": (
                v28_profile.PROFILE["reference_master_encoding"]
                if dual_display_delivery
                else "Rec.709 OETF / 1-1-1; BT.1886 reference display"
            ),
            "master_sha256": sha256(paths["scan"]),
            "quicktime_companion": (
                str(quicktime_paths["scan"])
                if dual_display_delivery else None
            ),
            "quicktime_companion_sha256": (
                sha256(quicktime_paths["scan"])
                if dual_display_delivery else None
            ),
        },
    }
    for name, manifest in manifests.items():
        (output_dirs[name] / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(timing, indent=2), flush=True)


if __name__ == "__main__":
    main()
