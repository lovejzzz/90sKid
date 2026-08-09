#!/usr/bin/env python3
"""Prototype process-isolated scan observer beside the parent projection."""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
from multiprocessing import shared_memory
from pathlib import Path
import time

import cv2
import numpy as np


def configure(workers: int) -> None:
    import emulsion_experiment as e
    import v27_accel
    import v27_production_accel
    import v34_profile

    v34_profile.apply(e)
    cv2.setNumThreads(4)
    v27_accel.apply(e, numba_threads=workers, array_workers=workers, exact_only=True)
    v27_accel.warm(e)
    v27_production_accel.apply(e)


def scan_worker(
    connection,
    mean_name: str,
    formed_name: str,
    output_name: str,
    shape: tuple[int, int, int],
    workers: int,
) -> None:
    configure(workers)
    import emulsion_experiment as e

    mean_shm = shared_memory.SharedMemory(name=mean_name)
    formed_shm = shared_memory.SharedMemory(name=formed_name)
    output_shm = shared_memory.SharedMemory(name=output_name)
    mean = np.ndarray(shape, dtype=np.float32, buffer=mean_shm.buf)
    formed = np.ndarray(shape, dtype=np.float32, buffer=formed_shm.buf)
    output = np.ndarray(shape, dtype=np.float32, buffer=output_shm.buf)
    connection.send("ready")
    while True:
        message = connection.recv()
        if message == "stop":
            break
        frame_index = int(message)
        started = time.perf_counter()
        scan = e.reconstruct_density_pair_to_display(
            mean,
            formed,
            frame_index,
            1.0,
            "cineon_bluray",
            "linear_rec709",
        )
        np.copyto(output, scan)
        connection.send(time.perf_counter() - started)
    mean_shm.close()
    formed_shm.close()
    output_shm.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("density_root", type=Path)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--frame-index", type=int, default=0)
    args = parser.parse_args()
    mean_source = np.load(args.density_root / "mean_density.npy", mmap_mode="r")
    formed_source = np.load(args.density_root / "formed_density.npy", mmap_mode="r")
    shape = tuple(mean_source.shape)
    nbytes = int(mean_source.nbytes)
    segments = [shared_memory.SharedMemory(create=True, size=nbytes) for _ in range(3)]
    try:
        mean = np.ndarray(shape, dtype=np.float32, buffer=segments[0].buf)
        formed = np.ndarray(shape, dtype=np.float32, buffer=segments[1].buf)
        scan_shared = np.ndarray(shape, dtype=np.float32, buffer=segments[2].buf)
        copy_started = time.perf_counter()
        np.copyto(mean, mean_source)
        np.copyto(formed, formed_source)
        input_copy_seconds = time.perf_counter() - copy_started
        context = mp.get_context("spawn")
        parent, child = context.Pipe()
        startup_started = time.perf_counter()
        process = context.Process(
            target=scan_worker,
            args=(
                child,
                segments[0].name,
                segments[1].name,
                segments[2].name,
                shape,
                args.workers,
            ),
        )
        process.start()
        if parent.recv() != "ready":
            raise RuntimeError("observer worker failed to initialize")
        startup_seconds = time.perf_counter() - startup_started
        configure(args.workers)
        import emulsion_experiment as e

        started = time.perf_counter()
        parent.send(args.frame_index)
        projection = e.reconstruct_density_pair_to_display(
            mean,
            formed,
            args.frame_index,
            1.0,
            "2383_projection_monitor",
            "linear_rec709",
        )
        child_seconds = float(parent.recv())
        parallel_seconds = time.perf_counter() - started
        scan_parallel = scan_shared.copy()
        started = time.perf_counter()
        projection_reference = e.reconstruct_density_pair_to_display(
            mean,
            formed,
            args.frame_index,
            1.0,
            "2383_projection_monitor",
            "linear_rec709",
        )
        scan_reference = e.reconstruct_density_pair_to_display(
            mean,
            formed,
            args.frame_index,
            1.0,
            "cineon_bluray",
            "linear_rec709",
        )
        sequential_seconds = time.perf_counter() - started
        parent.send("stop")
        process.join(30)
        result = {
            "shape": list(shape),
            "workers_per_process": args.workers,
            "input_shared_copy_seconds": input_copy_seconds,
            "worker_startup_seconds": startup_seconds,
            "parallel_observers_seconds": parallel_seconds,
            "child_scan_seconds": child_seconds,
            "sequential_observers_seconds": sequential_seconds,
            "steady_state_speedup": sequential_seconds / parallel_seconds,
            "projection_identical": bool(np.array_equal(projection, projection_reference)),
            "scan_identical": bool(np.array_equal(scan_parallel, scan_reference)),
            "projection_max_abs": float(np.max(np.abs(projection - projection_reference))),
            "scan_max_abs": float(np.max(np.abs(scan_parallel - scan_reference))),
            "child_exitcode": process.exitcode,
        }
        print(json.dumps(result, indent=2), flush=True)
    finally:
        for segment in segments:
            segment.close()
            segment.unlink()


if __name__ == "__main__":
    main()
