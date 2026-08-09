#!/usr/bin/env python3
"""Render deterministic and FSD controls beside the frozen V40 baseline."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v40_profile
from apply_v31_normal_process_adapter import adapt_frame_linear
from fsd_density import apply_fsd
from render_v23_dual_masters import save_srgb_still, sha256, summarize
from render_v40_dual_masters import PRINT_LUT, PRINT_LUT_SHA256


def xq_encoder(path: Path, width: int, height: int, fps: str) -> list[str]:
    command = e.prores_encoder_command(path, width, height, fps)
    command[command.index("-profile:v") + 1] = "5"
    return command


def deterministic_dual_observer(mean_density: np.ndarray, grain_scale: float) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate the V40 mean graph once per physical intermediate.

    The production dual renderer is structured for distinct mean and formed
    densities.  With both inputs identical it deliberately evaluates several
    zero-delta branches.  This reduced graph is the algebraic identity for a
    deterministic control and changes no observer, LUT, MTF, colour or gamut
    operation.
    """
    negative = e.apply_5279_mtf_to_record_density(mean_density, grain_scale)
    scanner_density = e.scanner_density_from_total_record_density(negative)
    scan = e.render_cineon_scan_master_from_scanner_density(
        e.apply_spirit_2k_scan_aperture_to_density(scanner_density)
    )
    scan = e.finish_cineon_scan_for_bluray(scan)
    scan = e.compress_oklab_chroma_to_rec709(scan)
    if e.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED:
        scan = e.neutralize_spirit_finished_gray_scale(scan)

    printer_density = e.negative_total_printer_density_from_record_density(negative)
    print_density = e.print_2383_density_from_negative(printer_density)
    print_density = e.apply_2383_mtf_to_print_density(print_density, grain_scale)
    projection = e.render_2383_monitor_projection_from_print_density(
        negative,
        print_density,
        scanner_density=scanner_density,
    )
    projection = e.compress_oklab_chroma_to_rec709(projection)
    # The V40 production graph performs its perceptual mean-preservation
    # boundary even when the stochastic delta is identically zero.  Retain
    # that floating-point boundary so the reduced graph is delivery-equivalent,
    # not merely algebraically equivalent in real arithmetic.
    projection = e.preserve_perceptual_grain_mean(projection, projection)
    return (
        np.clip(projection, 0.0, 1.0).astype(np.float32),
        np.clip(scan, 0.0, 1.0).astype(np.float32),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument("--site-count", type=int, default=176)
    parser.add_argument("--correlation-sigma", type=float, default=0.597)
    parser.add_argument("--density-strength", type=float, default=1.0)
    parser.add_argument("--opencv-threads", type=int, default=8)
    parser.add_argument("--numba-threads", type=int, default=8)
    parser.add_argument("--array-workers", type=int, default=8)
    parser.add_argument(
        "--fsd-only",
        action="store_true",
        help="render only the FSD branch while still evaluating its deterministic source",
    )
    parser.add_argument(
        "--reference-deterministic-graph",
        action="store_true",
        help="retain the duplicate zero-delta paths for equivalence auditing",
    )
    args = parser.parse_args()
    if args.frames < 1:
        raise ValueError("frames must be positive")
    if sha256(PRINT_LUT) != PRINT_LUT_SHA256:
        raise ValueError("validated V40 print LUT hash mismatch")

    v40_profile.apply(e)
    e._PRINT_2383_MONITOR_OUTPUT_LUT = np.load(PRINT_LUT, allow_pickle=False)
    cv2.setNumThreads(args.opencv_threads)
    import v27_accel

    v27_accel.apply(
        e,
        numba_threads=args.numba_threads,
        array_workers=args.array_workers,
        exact_only=True,
    )
    v27_accel.warm(e)

    width, height, fps = e.probe_video(args.input)
    branches = {"fsd": args.output / "fsd"}
    if not args.fsd_only:
        branches = {"deterministic": args.output / "deterministic", **branches}
    for directory in branches.values():
        directory.mkdir(parents=True, exist_ok=True)
    master_paths = {
        name: directory / "05_emulsion_master_prores4444.mov"
        for name, directory in branches.items()
    }
    companion_paths = {
        name: directory / "06_quicktime_preview_srgb_prores4444.mov"
        for name, directory in branches.items()
    }
    encoders = {
        name: subprocess.Popen(
            xq_encoder(path, width, height, fps), stdin=subprocess.PIPE
        )
        for name, path in master_paths.items()
    }
    companion_encoders = {
        name: subprocess.Popen(
            xq_encoder(path, width, height, fps), stdin=subprocess.PIPE
        )
        for name, path in companion_paths.items()
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
    fsd_stats: list[dict[str, float | int | str]] = []
    stages: dict[str, list[float]] = {
        "decode_read": [],
        "scene_and_mean_negative": [],
        "deterministic_dual_observer": [],
        "fsd_density_formation": [],
        "encode_write_four": [],
    }
    total_start = time.perf_counter()
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
            raw_colour=v40_profile.PROFILE["raw_colour"],
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.film_records_from_rgb(film)
        mean_density = e.develop_5279_record_density(records)
        stages["scene_and_mean_negative"].append(time.perf_counter() - mark)

        frame_number = args.start_frame + processed
        mark = time.perf_counter()
        if args.reference_deterministic_graph:
            projection, scan = e.reconstruct_density_pair_to_dual_display_v39(
                mean_density,
                mean_density,
                frame_number,
                args.grain_scale,
                "linear_rec709",
            )
        else:
            projection, scan = deterministic_dual_observer(
                mean_density, args.grain_scale
            )
        deterministic = adapt_frame_linear(
            projection,
            scan,
            v40_profile.PROFILE.get(
                "final_adapter_opponent_high_frequency_retention", 0.0
            ),
        ).astype(np.float32)
        stages["deterministic_dual_observer"].append(time.perf_counter() - mark)
        del raw, film, records, mean_density, projection, scan

        mark = time.perf_counter()
        fsd, frame_stats = apply_fsd(
            deterministic,
            frame_number,
            site_count=args.site_count,
            correlation_sigma=args.correlation_sigma,
            density_strength=args.density_strength,
        )
        frame_stats["absolute_frame"] = frame_number
        fsd_stats.append(frame_stats)
        stages["fsd_density_formation"].append(time.perf_counter() - mark)

        linear_images = {"fsd": fsd}
        if not args.fsd_only:
            linear_images = {"deterministic": deterministic, **linear_images}
        companion_images = {
            name: e.srgb_encode(image).astype(np.float32)
            for name, image in linear_images.items()
        }
        master_images = {
            name: e.bt1886_reference_encode(image).astype(np.float32)
            for name, image in linear_images.items()
        }
        mark = time.perf_counter()
        for name, image in master_images.items():
            encoded = np.rint(np.clip(image, 0.0, 1.0) * 65535.0).astype("<u2")
            assert encoders[name].stdin is not None
            encoders[name].stdin.write(encoded.tobytes())
        for name, image in companion_images.items():
            encoded = np.rint(np.clip(image, 0.0, 1.0) * 65535.0).astype("<u2")
            assert companion_encoders[name].stdin is not None
            companion_encoders[name].stdin.write(encoded.tobytes())
        stages["encode_write_four"].append(time.perf_counter() - mark)
        if processed == representative_index:
            representative = {
                name: image.copy() for name, image in companion_images.items()
            }
        del deterministic, fsd, linear_images, master_images, companion_images
        processed += 1
        elapsed = time.perf_counter() - total_start
        eta = elapsed / processed * (args.frames - processed)
        print(
            f"FSD comparator frame {processed}/{args.frames} · "
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
            raise RuntimeError(f"{name} master encoder failed")
        e.finalize_prores_rec709_metadata(master_paths[name])
    for name, encoder in companion_encoders.items():
        assert encoder.stdin is not None
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError(f"{name} companion encoder failed")
        e.finalize_prores_srgb_metadata(companion_paths[name])
    for name, image in representative.items():
        save_srgb_still(branches[name] / "still_emulsion.jpg", image)

    total_seconds = time.perf_counter() - total_start
    profile_name = v40_profile.PROFILE["short_name"]
    timing = {
        "clock": "time.perf_counter monotonic wall clock",
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "opencv_threads": args.opencv_threads,
            "numba_threads": args.numba_threads,
            "array_workers": args.array_workers,
        },
        "pipeline": f"{profile_name} Finite-Site Density (FSD) comparator",
        "stage_summaries": {
            name: summarize(values) for name, values in stages.items()
        },
        "total_wall_seconds_before_hashes": total_seconds,
        "encoded_comparator_branches": list(branches),
        "effective_seconds_per_frame": total_seconds / processed,
    }
    (args.output / "timing.json").write_text(
        json.dumps(timing, indent=2) + "\n", encoding="utf-8"
    )
    common = {
        "release": f"{profile_name} comparator · Finite-Site Density (FSD)",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "input_dimensions": [width, height],
        "fps": fps,
        "start_frame": args.start_frame,
        "frames_processed": processed,
        "exposure_stops": args.exposure_stops,
        "observer": f"{profile_name} deterministic 5279 mean → 2383 → final normal-process adapter",
        "deterministic_graph": (
            "reference duplicate zero-delta graph"
            if args.reference_deterministic_graph
            else "algebraically reduced exact mean graph"
        ),
        "artistic_grade": "none",
        "fsd_contract": {
            "density_lookup": "512x512 inverse Binomial CDF / N",
            "uniform_contract": "open-interval uniform variate confirmed from the recovered Silver Efex lookup",
            "moving_field": "deterministic frame-seeded PCG64DXSM; isotropic and non-repeating at native resolution",
            "density_domain": f"IEC 61966-2-1 signal after the deterministic {profile_name} observer",
            "tone_mix": "Y'=(1-alpha)Y+alpha*G; alpha=strength*A(Y)",
            "spatial_model": "Gaussian-copula correlation; no Nik branded-film texture",
            "colour_model": f"deterministic {profile_name} signal-domain opponent field held fixed; density excursion is gamut-limited before composition; no independent RGB impulses",
            "site_count": args.site_count,
            "correlation_sigma_native_px": args.correlation_sigma,
            "density_strength": args.density_strength,
        },
        "fsd_frame_stats": fsd_stats,
        "renderer_sha256": sha256(Path(__file__)),
        "fsd_algorithm_sha256": sha256(Path(apply_fsd.__code__.co_filename)),
        "v40_profile_sha256": sha256(Path(v40_profile.__file__)),
        "active_profile": profile_name,
        "profile_sha256": sha256(Path(v40_profile.__file__)),
        "print_lut_sha256": PRINT_LUT_SHA256,
        "timing": timing,
        "command": [sys.executable, *sys.argv],
    }
    manifests = {
        "fsd": {
            **common,
            "branch": "FSD finite-site density",
            "master_sha256": sha256(master_paths["fsd"]),
            "companion_sha256": sha256(companion_paths["fsd"]),
        },
    }
    if not args.fsd_only:
        manifests = {
            "deterministic": {
                **common,
                "branch": "deterministic no-grain control",
                "master_sha256": sha256(master_paths["deterministic"]),
                "companion_sha256": sha256(companion_paths["deterministic"]),
            },
            **manifests,
        }
    for name, manifest in manifests.items():
        (branches[name] / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(timing, indent=2), flush=True)


if __name__ == "__main__":
    main()
