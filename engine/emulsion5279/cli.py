"""Command-line renderer for explicit, versioned 5279 engine profiles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import time

import numpy as np

from .contracts import EngineConfig, EngineMode
from .io import (
    DualDeliveryWriter,
    ProResRawDecoder,
    rebuild_scale_integrated_srgb_review_from_master,
    retain_source_audio_and_timecode,
)
from .pipeline import Emulsion5279Engine


def _summarize(rows: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for stage in rows[0]:
        values = np.asarray([row[stage] for row in rows], dtype=np.float64)
        result[stage] = {
            "total_seconds": float(values.sum()),
            "mean_seconds_per_frame": float(values.mean()),
            "p95_seconds_per_frame": float(np.percentile(values, 95)),
        }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=1)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument("--oversample", type=int, default=1)
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in EngineMode],
        default=EngineMode.PRODUCTION_METAL.value,
    )
    parser.add_argument("--opencv-threads", type=int, default=8)
    parser.add_argument("--binomial-workers", type=int, default=8)
    parser.add_argument("--numba-threads", type=int, default=8)
    parser.add_argument("--array-workers", type=int, default=8)
    parser.add_argument(
        "--observer-branch-workers",
        type=int,
        choices=(1, 2),
        default=1,
        help=(
            "schedule projection and scan sequentially (1) or concurrently "
            "(2); pixels are identical, but native-frame memory and speed "
            "depend on the machine"
        ),
    )
    parser.add_argument("--grain-domain-salt", type=int, default=0)
    parser.add_argument(
        "--profile",
        choices=(
            "v42", "v43h", "v44", "v45", "v46", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"
        ),
        default="v42",
    )
    parser.add_argument(
        "--review-width",
        type=int,
        default=1920,
        help=(
            "V44 display-review width; native masters remain at source resolution"
        ),
    )
    parser.add_argument(
        "--experimental-overrides",
        action="store_true",
        help="permit non-baseline exposure/grain controls and mark the result experimental",
    )
    parser.add_argument(
        "--cineon-dpx",
        action="store_true",
        help=(
            "also write code-exact 10-bit RGB printing-density DPX frames; "
            "these are exchange data, not display-ready images"
        ),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.frames < 1:
        raise ValueError("frames must be positive")
    config = EngineConfig(
        profile=args.profile,
        exposure_stops=args.exposure_stops,
        grain_scale=args.grain_scale,
        oversample=args.oversample,
        mode=EngineMode(args.mode),
        opencv_threads=args.opencv_threads,
        binomial_workers=args.binomial_workers,
        numba_threads=args.numba_threads,
        array_workers=args.array_workers,
        observer_branch_workers=args.observer_branch_workers,
        grain_domain_salt=args.grain_domain_salt,
        research_baseline=not args.experimental_overrides,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    timings: list[dict[str, float]] = []
    with ProResRawDecoder(
        args.decoder, args.input, args.start_frame, args.frames
    ) as decoder:
        with DualDeliveryWriter(
            args.output,
            decoder.width,
            decoder.height,
            decoder.fps,
            args.frames,
            cineon_dpx=args.cineon_dpx,
            start_frame=args.start_frame,
        ) as writer:
            for offset, (absolute_frame, raw) in enumerate(decoder):
                frame = engine.render_frame(raw, absolute_frame)
                writer.write(frame)
                timings.append(dict(frame.stage_seconds))
                elapsed = time.perf_counter() - started
                eta = elapsed / (offset + 1) * (args.frames - offset - 1)
                print(
                    f"{args.profile.upper()} frame {offset + 1}/{args.frames} · "
                    f"elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
                    flush=True,
                )

    engine.validate_rendered_frames(args.frames)
    finalization_started = time.perf_counter()
    review_sampling: dict[str, object] | None = None
    additional_srgb_movies: tuple[str, ...] = ()
    if args.profile in ("v44", "v45", "v46", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"):
        review_name = "07_scale_integrated_review_srgb_prores4444.mov"
        review_sampling = {}
        for directory in ("projection", "bluray_scan"):
            root = args.output / directory
            review_sampling[directory] = (
                rebuild_scale_integrated_srgb_review_from_master(
                    root / "05_emulsion_master_prores4444.mov",
                    root / review_name,
                    args.frames,
                    args.review_width,
                )
            )
        additional_srgb_movies = (review_name,)
    source_delivery = retain_source_audio_and_timecode(
        args.output,
        args.input,
        args.start_frame,
        args.frames,
        decoder.fps,
        version_label=args.profile.upper(),
        additional_srgb_movies=additional_srgb_movies,
    )
    source_delivery["seconds"] = time.perf_counter() - finalization_started

    report = {
        "engine": engine.provenance,
        "input": str(args.input),
        "start_frame": args.start_frame,
        "frames": args.frames,
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "config": {
            "exposure_stops": config.exposure_stops,
            "grain_scale": config.grain_scale,
            "oversample": config.oversample,
            "mode": config.mode.value,
            "opencv_threads": config.opencv_threads,
            "binomial_workers": config.binomial_workers,
            "numba_threads": config.numba_threads,
            "array_workers": config.array_workers,
            "observer_branch_workers": config.observer_branch_workers,
            "grain_domain_salt": config.grain_domain_salt,
            "research_baseline": config.research_baseline,
            "cineon_dpx": args.cineon_dpx,
        },
        "stage_summaries": _summarize(timings),
        "source_delivery": source_delivery,
        "review_sampling": review_sampling,
        "cineon_exchange": (
            {
                "path": str(args.output / "cineon_printing_density"),
                "frame_range": [
                    args.start_frame,
                    args.start_frame + args.frames - 1,
                ],
                "contract": engine.provenance["cineon_exchange_contract"],
            }
            if args.cineon_dpx
            else None
        ),
        "total_wall_seconds": time.perf_counter() - started,
    }
    (args.output / "timing.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
