#!/usr/bin/env python3
"""Render V27 scan segments concurrently and concatenate them without re-encoding."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

import emulsion_experiment as e
from render_v23_dual_masters import save_still, sha256
from render_v27_scan_master import hardlink_or_copy


def split_ranges(start: int, frames: int, workers: int) -> list[tuple[int, int]]:
    workers = max(1, min(workers, frames))
    base, remainder = divmod(frames, workers)
    ranges: list[tuple[int, int]] = []
    cursor = start
    for index in range(workers):
        count = base + (1 if index < remainder else 0)
        ranges.append((cursor, count))
        cursor += count
    return ranges


def concat_escape(path: Path) -> str:
    return str(path.resolve()).replace("'", "'\\''")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--reuse-v26-projection", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--worker-opencv-threads", type=int, default=0)
    parser.add_argument("--worker-binomial-workers", type=int, default=0)
    parser.add_argument("--worker-numba-threads", type=int, default=0)
    parser.add_argument("--worker-array-workers", type=int, default=0)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument("--oversample", type=int, default=1)
    parser.add_argument("--metal-gaussian-production", action="store_true")
    args = parser.parse_args()

    if args.frames < 1:
        raise ValueError("frames must be positive")
    if args.metal_gaussian_production and args.workers > 1:
        raise ValueError(
            "Metal production mode must use one renderer on this M4 Max: "
            "multiple processes contend for the same GPU and benchmark slower. "
            "Use render_v27_scan_master.py for Metal latency, or omit "
            "--metal-gaussian-production for the faster two-worker batch path."
        )
    width, height, fps = e.probe_video(args.input)
    ranges = split_ranges(args.start_frame, args.frames, args.workers)
    multiple = len(ranges) > 1
    worker_opencv = args.worker_opencv_threads or (8 if multiple else 16)
    worker_binomial = args.worker_binomial_workers or (8 if multiple else 12)
    worker_numba = args.worker_numba_threads or (8 if multiple else 12)
    worker_array = args.worker_array_workers or (8 if multiple else 12)
    output_scan = args.output / "bluray_scan"
    output_projection = args.output / "projection"
    output_scan.mkdir(parents=True, exist_ok=True)
    output_projection.mkdir(parents=True, exist_ok=True)
    final_scan = output_scan / "05_emulsion_master_prores4444.mov"
    renderer = Path(__file__).with_name("render_v27_scan_master.py")
    wall_started = time.perf_counter()

    segment_reports: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="v27-parallel-") as temporary:
        temporary_root = Path(temporary)
        processes: list[tuple[subprocess.Popen[str], Path, int, int]] = []
        for index, (segment_start, segment_frames) in enumerate(ranges):
            segment_output = temporary_root / f"segment_{index:02d}"
            command = [
                sys.executable,
                str(renderer),
                str(args.input),
                str(segment_output),
                "--decoder",
                str(args.decoder),
                "--reuse-v26-projection",
                str(args.reuse_v26_projection),
                "--start-frame",
                str(segment_start),
                "--frames",
                str(segment_frames),
                "--exposure-stops",
                str(args.exposure_stops),
                "--grain-scale",
                str(args.grain_scale),
                "--oversample",
                str(args.oversample),
                "--opencv-threads",
                str(worker_opencv),
                "--binomial-workers",
                str(worker_binomial),
                "--numba-threads",
                str(worker_numba),
                "--array-workers",
                str(worker_array),
                "--accelerated-cpu-exact",
            ]
            if args.metal_gaussian_production:
                command.append("--metal-gaussian-production")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            processes.append((process, segment_output, segment_start, segment_frames))

        segment_paths: list[Path] = []
        for process, segment_output, segment_start, segment_frames in processes:
            stdout, _ = process.communicate()
            if process.returncode != 0:
                raise RuntimeError(
                    f"segment {segment_start}+{segment_frames} failed:\n{stdout}"
                )
            segment_path = (
                segment_output
                / "bluray_scan"
                / "05_emulsion_master_prores4444.mov"
            )
            segment_paths.append(segment_path)
            timing = json.loads((segment_output / "timing.json").read_text())
            segment_reports.append(
                {
                    "start_frame": segment_start,
                    "frames": segment_frames,
                    "wall_seconds": timing[
                        "render_and_finalize_wall_seconds_before_hashes"
                    ],
                    "stage_summaries": timing["stage_summaries"],
                }
            )

        concat_list = temporary_root / "concat.txt"
        concat_list.write_text(
            "".join(f"file '{concat_escape(path)}'\n" for path in segment_paths),
            encoding="utf-8",
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(final_scan),
            ],
            check=True,
        )
        e.finalize_prores_rec709_metadata(final_scan)

    representative_index = args.frames // 2
    raw = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(final_scan),
            "-vf",
            f"select=eq(n\\,{representative_index})",
            "-frames:v",
            "1",
            "-pix_fmt",
            "rgb48le",
            "-f",
            "rawvideo",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    representative = np.frombuffer(raw, dtype="<u2").reshape(height, width, 3)
    save_still(
        output_scan / "still_emulsion.jpg",
        representative.astype(np.float32) / 65535.0,
        "scan",
    )

    projection_master = args.reuse_v26_projection / "05_emulsion_master_prores4444.mov"
    projection_still = args.reuse_v26_projection / "still_emulsion.jpg"
    projection_method = hardlink_or_copy(
        projection_master, output_projection / projection_master.name
    )
    hardlink_or_copy(projection_still, output_projection / projection_still.name)

    wall_seconds = time.perf_counter() - wall_started
    timing = {
        "clock": "time.perf_counter monotonic wall clock",
        "architecture": (
            "one production-Metal renderer; lossless ProRes concat"
            if args.metal_gaussian_production
            else "low-memory CPU frame-range workers; lossless ProRes concat"
        ),
        "workers": len(ranges),
        "worker_threads": {
            "opencv": worker_opencv,
            "binomial": worker_binomial,
            "numba": worker_numba,
            "array": worker_array,
        },
        "segments": segment_reports,
        "wall_seconds": wall_seconds,
        "effective_seconds_per_frame": wall_seconds / args.frames,
        "frames_per_wall_second": args.frames / wall_seconds,
        "projection_reuse": projection_method,
    }
    (args.output / "timing.json").write_text(
        json.dumps(timing, indent=2) + "\n", encoding="utf-8"
    )
    # Keep the combined manifest concise; segment details and per-stage timings
    # are preserved in timing.json.
    manifest = {
        "release": "V27 neutral-scale constrained period 2K scan",
        "profile": "v27-accelerated-cpu-exact-parallel",
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "input_dimensions": [width, height],
        "fps": fps,
        "start_frame": args.start_frame,
        "frames_processed": args.frames,
        "duration_seconds": args.frames / (24000.0 / 1001.0),
        "viewing_look": "cineon_bluray",
        "output_encoding": "Rec.709 OETF / 1-1-1; BT.1886 reference display",
        "master_sha256": sha256(final_scan),
        "quality_constraint": "decoded pixels bit-exact to the V27 reference path",
        "parallel_timing": timing,
    }
    if args.metal_gaussian_production:
        manifest["quality_constraint"] = (
            "production numerical parity; Archive exact remains CPU bit-exact"
        )
        manifest["profile"] = "v27-accelerated-production-metal-parallel"
    (output_scan / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    projection_manifest = {
        **manifest,
        "viewing_look": "2383_projection_monitor",
        "master_sha256": sha256(output_projection / projection_master.name),
        "reused_bit_exact_from_v26": True,
    }
    (output_projection / "manifest.json").write_text(
        json.dumps(projection_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(timing, indent=2), flush=True)


if __name__ == "__main__":
    main()
