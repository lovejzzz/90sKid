#!/usr/bin/env python3
"""Render V46 deterministic observers through the experimental SHM branch."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path

from engine.emulsion5279 import legacy
from engine.emulsion5279.contracts import DeliveryEncoding, EngineConfig, EngineMode
from engine.emulsion5279.io import (
    ProResRawDecoder,
    _Writer,
    rebuild_scale_integrated_srgb_review_from_master,
    rebuild_srgb_companion_from_master,
)
from engine.emulsion5279.pipeline import Emulsion5279Engine

from render_v23_dual_masters import sha256
from shm_density import DEFAULT_PROFILE, apply_shm


BRANCHES = {
    "deterministic_projection": "deterministic_projection",
    "deterministic_scan": "deterministic_scan",
    "shm_projection": "shm_projection",
    "shm_scan": "shm_scan",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument("--review-width", type=int, default=1920)
    parser.add_argument(
        "--shm-only",
        action="store_true",
        help="encode only the two SHM observers after the paired probe is accepted",
    )
    args = parser.parse_args()
    if args.frames < 1:
        raise ValueError("frames must be positive")

    config = EngineConfig(
        profile="v46",
        mode=EngineMode.PRODUCTION_METAL,
        observer_branch_workers=1,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    args.output.mkdir(parents=True, exist_ok=True)
    active_branches = (
        {name: directory for name, directory in BRANCHES.items() if name.startswith("shm_")}
        if args.shm_only
        else BRANCHES
    )
    timings: dict[str, list[float]] = {
        "negative_and_deterministic_observers": [],
        "shm_projection": [],
        "shm_scan": [],
        "encode_write_four": [],
    }
    stats: dict[str, list[dict[str, object]]] = {
        "shm_projection": [],
        "shm_scan": [],
    }
    started = time.perf_counter()
    writers: dict[str, _Writer] = {}
    width = height = 0
    fps = ""
    try:
        with ProResRawDecoder(
            args.decoder, args.input, args.start_frame, args.frames
        ) as decoder:
            width, height, fps = decoder.width, decoder.height, decoder.fps
            for name, directory in active_branches.items():
                writers[name] = _Writer.open(
                    args.output / directory / "05_emulsion_master_prores4444.mov",
                    DeliveryEncoding.REFERENCE_BT1886,
                    width,
                    height,
                    fps,
                )
            for offset, (absolute_frame, raw) in enumerate(decoder):
                mark = time.perf_counter()
                negative = engine.form_negative(raw, absolute_frame)
                _, mean = engine.observe_with_mean(negative, absolute_frame)
                timings["negative_and_deterministic_observers"].append(
                    time.perf_counter() - mark
                )

                deterministic_projection = mean.projection_linear_rec709
                deterministic_scan = mean.scan_linear_rec709
                mark = time.perf_counter()
                shm_projection, projection_stats = apply_shm(
                    deterministic_projection, absolute_frame
                )
                timings["shm_projection"].append(time.perf_counter() - mark)
                mark = time.perf_counter()
                shm_scan, scan_stats = apply_shm(deterministic_scan, absolute_frame)
                timings["shm_scan"].append(time.perf_counter() - mark)
                projection_stats["absolute_frame"] = absolute_frame
                scan_stats["absolute_frame"] = absolute_frame
                stats["shm_projection"].append(projection_stats)
                stats["shm_scan"].append(scan_stats)

                images = {
                    "deterministic_projection": deterministic_projection,
                    "deterministic_scan": deterministic_scan,
                    "shm_projection": shm_projection,
                    "shm_scan": shm_scan,
                }
                if args.shm_only:
                    images = {
                        name: image
                        for name, image in images.items()
                        if name.startswith("shm_")
                    }
                mark = time.perf_counter()
                for name, image in images.items():
                    writers[name].write(legacy.model.bt1886_reference_encode(image))
                timings["encode_write_four"].append(time.perf_counter() - mark)
                del raw, negative, mean, images
                del deterministic_projection, deterministic_scan
                del shm_projection, shm_scan
                elapsed = time.perf_counter() - started
                eta = elapsed / (offset + 1) * (args.frames - offset - 1)
                print(
                    f"V47 SHM frame {offset + 1}/{args.frames} · "
                    f"elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
                    flush=True,
                )
        for writer in writers.values():
            writer.close()
    except Exception:
        for writer in writers.values():
            if writer.process.stdin is not None:
                writer.process.stdin.close()
            writer.process.terminate()
            writer.process.wait()
        raise
    finally:
        engine.close()

    engine.validate_rendered_frames(args.frames)
    reviews: dict[str, object] = {}
    for name, directory in active_branches.items():
        root = args.output / directory
        master = root / "05_emulsion_master_prores4444.mov"
        companion = root / "06_quicktime_preview_srgb_prores4444.mov"
        rebuild_srgb_companion_from_master(master, companion, args.frames)
        reviews[name] = rebuild_scale_integrated_srgb_review_from_master(
            master,
            root / "07_scale_integrated_review_srgb_prores4444.mov",
            args.frames,
            args.review_width,
        )

    def summarize(values: list[float]) -> dict[str, float]:
        return {
            "total_seconds": float(sum(values)),
            "mean_seconds_per_frame": float(sum(values) / len(values)),
            "maximum_seconds": float(max(values)),
        }

    common = {
        "release": "V47 SHM experimental comparator",
        "release_class": "independent_same_class_silver_halide_morphology",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "start_frame": args.start_frame,
        "frames": args.frames,
        "dimensions": [width, height],
        "fps": fps,
        "source_observer": "V46 deterministic mean; no V46 physical grain",
        "shm_profile": DEFAULT_PROFILE.__dict__,
        "evidence_boundary": (
            "SHM implements confirmed Silver Efex finite-site, tone taper and "
            "Rec.601 density-axis behavior with independently generated "
            "multiscale morphology. It is not DxO/Nik code, a copied stock "
            "patch, a pixel-identical replica, or a measured 5279 morphology."
        ),
        "artistic_grade": "none",
    }
    for name, directory in active_branches.items():
        root = args.output / directory
        manifest = {
            **common,
            "branch": name,
            "master_sha256": sha256(root / "05_emulsion_master_prores4444.mov"),
            "companion_sha256": sha256(
                root / "06_quicktime_preview_srgb_prores4444.mov"
            ),
            "scale_integrated_review": reviews[name],
        }
        if name in stats:
            manifest["shm_frame_stats"] = stats[name]
        (root / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    report = {
        **common,
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "stage_summaries": {
            name: summarize(values) for name, values in timings.items()
        },
        "total_wall_seconds": time.perf_counter() - started,
    }
    (args.output / "timing.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
