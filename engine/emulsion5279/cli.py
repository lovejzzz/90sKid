"""Command-line renderer for the explicit-stage second-generation engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import time

import numpy as np

from .contracts import EngineConfig, EngineMode
from .io import DualDeliveryWriter, ProResRawDecoder
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
        default=EngineMode.ARCHIVE_EXACT_CPU.value,
    )
    parser.add_argument("--opencv-threads", type=int, default=8)
    parser.add_argument("--binomial-workers", type=int, default=8)
    parser.add_argument("--numba-threads", type=int, default=8)
    parser.add_argument("--array-workers", type=int, default=8)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.frames < 1:
        raise ValueError("frames must be positive")
    config = EngineConfig(
        exposure_stops=args.exposure_stops,
        grain_scale=args.grain_scale,
        oversample=args.oversample,
        mode=EngineMode(args.mode),
        opencv_threads=args.opencv_threads,
        binomial_workers=args.binomial_workers,
        numba_threads=args.numba_threads,
        array_workers=args.array_workers,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    timings: list[dict[str, float]] = []
    representative = None
    with ProResRawDecoder(
        args.decoder, args.input, args.start_frame, args.frames
    ) as decoder:
        with DualDeliveryWriter(
            args.output, decoder.width, decoder.height, decoder.fps
        ) as writer:
            for offset, (absolute_frame, raw) in enumerate(decoder):
                frame = engine.render_frame(raw, absolute_frame)
                writer.write(frame)
                timings.append(dict(frame.stage_seconds))
                if offset == args.frames // 2:
                    representative = frame
                elapsed = time.perf_counter() - started
                eta = elapsed / (offset + 1) * (args.frames - offset - 1)
                print(
                    f"V41-v2 frame {offset + 1}/{args.frames} · "
                    f"elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
                    flush=True,
                )
            if representative is None:
                raise RuntimeError("no representative frame was rendered")
            writer.save_stills(representative)

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
        },
        "stage_summaries": _summarize(timings),
        "total_wall_seconds": time.perf_counter() - started,
    }
    (args.output / "timing.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
