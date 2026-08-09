#!/usr/bin/env python3
"""Quality-aware M4 Max scheduler for the optimized V27 renderer."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


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
    parser.add_argument(
        "--policy",
        choices=("archive-exact", "production-float32", "fastest"),
        default="archive-exact",
        help="select exact CPU, OFX-like float32 CPU, or fastest Metal for one frame",
    )
    parser.add_argument(
        "--throughput",
        choices=("balanced", "maximum"),
        default="balanced",
        help="select the measured safe or best-throughput M4 Max topology",
    )
    args = parser.parse_args()
    if args.frames < 1:
        raise ValueError("frames must be positive")

    source_dir = Path(__file__).parent
    common = [
        str(args.input),
        str(args.output),
        "--decoder",
        str(args.decoder),
        "--reuse-v26-projection",
        str(args.reuse_v26_projection),
        "--start-frame",
        str(args.start_frame),
        "--frames",
        str(args.frames),
        "--exposure-stops",
        str(args.exposure_stops),
        "--grain-scale",
        str(args.grain_scale),
        "--oversample",
        str(args.oversample),
    ]

    if args.frames >= 2:
        renderer = source_dir / "render_v27_parallel_scan_master.py"
        requested_maximum = args.throughput == "maximum" and args.frames >= 3
        # Exact row-parallel layer work changed the topology result: two 8-way
        # workers now beat three 5-way workers while also avoiding swap pressure.
        workers = 2
        per_worker = 8
        command = [
            sys.executable,
            str(renderer),
            *common,
            "--workers",
            str(workers),
            "--worker-opencv-threads",
            str(per_worker),
            "--worker-binomial-workers",
            str(per_worker),
            "--worker-numba-threads",
            str(per_worker),
            "--worker-array-workers",
            str(per_worker),
        ]
        selected = "dual-cpu-best-measured-throughput"
        parity = "Archive exact; decoded pixels bit-exact to V27"
        if requested_maximum:
            reason = (
                "Maximum was re-profiled after exact row-parallel layer work: "
                "two 8/8/8/8 workers now measure 15.08 s/frame, so the "
                "scheduler keeps the faster and lower-pressure dual topology."
            )
        else:
            reason = (
                "Two 8/8/8/8 CPU workers measured 15.08 s/frame with exact "
                "V27 decoded pixels and beat the three-worker topology."
            )
    else:
        renderer = source_dir / "render_v27_scan_master.py"
        command = [
            sys.executable,
            str(renderer),
            *common,
            "--opencv-threads",
            "16",
            "--binomial-workers",
            "12",
            "--numba-threads",
            "12",
            "--array-workers",
            "12",
            "--accelerated-cpu-exact",
        ]
        if args.policy == "fastest":
            command.append("--metal-gaussian-production")
            selected = "single-metal-production-latency"
            parity = "Production numerical parity; not Archive bit-exact"
            reason = (
                "Float32 + Metal measured 19.24 s/frame; 99.99533% of 12-bit "
                "channel codes matched Archive exact and PSNR was 113.69 dB."
            )
        elif args.policy == "production-float32":
            command.append("--production-float32-spatial")
            selected = "single-cpu-production-float32"
            parity = "Production float32 parity; not Archive bit-exact"
            reason = (
                "Float32 CPU measured 21.28 s/frame versus 21.62 s for Archive "
                "exact. Its 0.34 s gain no longer justifies leaving bit-exact "
                "quality; retain only as an OFX engineering reference."
            )
        else:
            selected = "single-cpu-archive-exact"
            parity = "Archive exact; decoded pixels bit-exact to V27"
            reason = (
                "Strict CPU measured 21.62 s/frame and preserves every V27 bit; "
                "this remains the quality-first default."
            )

    decision = {
        "machine_profile": "Apple M4 Max 16-core CPU / 40-core GPU / 48 GB",
        "requested_policy": args.policy,
        "requested_throughput": args.throughput,
        "frames": args.frames,
        "selected_path": selected,
        "parity": parity,
        "reason": reason,
        "command": command,
    }
    print(json.dumps(decision, indent=2), flush=True)
    started = time.perf_counter()
    subprocess.run(command, check=True)
    decision["scheduler_wall_seconds"] = time.perf_counter() - started
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "scheduler.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
