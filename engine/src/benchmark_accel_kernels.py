#!/usr/bin/env python3
"""Compare experimental kernels against V27's reference NumPy path."""

from __future__ import annotations

import argparse
import gc
import json
import time
from pathlib import Path

import cv2
import numpy as np
from numba import set_num_threads

import emulsion_experiment as e
import pipeline_accel as accel
import v27_profile


def measure(function, *args):
    started = time.perf_counter()
    result = function(*args)
    return result, time.perf_counter() - started


def error(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    delta = np.abs(reference.astype(np.float32) - candidate.astype(np.float32))
    return {
        "maximum": float(delta.max()),
        "mean": float(delta.mean()),
        "p99_9": float(np.percentile(delta, 99.9)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--density", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--numba-threads", type=int, default=12)
    args = parser.parse_args()

    v27_profile.apply(e)
    cv2.setNumThreads(16)
    set_num_threads(args.numba_threads)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw = np.load(args.raw, mmap_mode="r")

    matrix = np.asarray(e.BT2020_TO_XYZ_D65, dtype=np.float32)
    matrix_reference, matrix_numpy_seconds = measure(
        np.einsum, "...c,dc->...d", raw, matrix
    )
    matrix_candidate, matrix_cv_seconds = measure(cv2.transform, raw, matrix)
    result: dict[str, object] = {
        "numba_threads": args.numba_threads,
        "matrix": {
            "numpy_seconds": matrix_numpy_seconds,
            "opencv_seconds": matrix_cv_seconds,
            "speedup": matrix_numpy_seconds / matrix_cv_seconds,
            "error": error(matrix_reference, matrix_candidate),
        }
    }
    del matrix_reference, matrix_candidate
    gc.collect()

    encoded = e.vlog_encode(np.asarray(raw) * np.float32(2.0**0.45))
    lut = e.load_panasonic_raw_to_vgamut_lut()
    # Compile on a small array before measuring the native frame.
    accel.camera_cube_trilinear(encoded[:4, :4], lut)
    camera_reference, camera_numpy_seconds = measure(e.apply_rgb_cube_lut, encoded, lut)
    camera_candidate, camera_numba_seconds = measure(
        accel.camera_cube_trilinear, encoded, lut
    )
    result["camera_cube"] = {
        "numpy_seconds": camera_numpy_seconds,
        "numba_seconds": camera_numba_seconds,
        "speedup": camera_numpy_seconds / camera_numba_seconds,
        "error": error(camera_reference, camera_candidate),
    }
    del encoded, camera_reference, camera_candidate
    gc.collect()

    film = e.scene_to_5279_film_rgb(
        np.asarray(raw), 0.45, "panasonic_official", True, "photochemical"
    )
    records = e.film_records_from_rgb(film)
    log_exposure = np.log10(np.maximum(records, 1e-8)) - 1.0
    accel.record_density_mix_fused(
        log_exposure[:4, :4],
        e.SENSITO_LOG_EXPOSURE,
        e.SENSITO_DENSITY_RGB,
        e.SUBEMULSION_FAST_CENTRE_LOGE_RGB,
        e.SUBEMULSION_SPEED_OFFSETS_LOGE,
        e.SUBEMULSION_TRANSITION_WIDTH_RGB,
        e.SUBEMULSION_CAPACITY_FRACTIONS,
        e.SUBEMULSION_DYE_RECORD_MIX,
    )
    record_reference, record_numpy_seconds = measure(
        e.record_densities_from_log_exposure, log_exposure
    )
    record_candidate, record_numba_seconds = measure(
        accel.record_density_mix_fused,
        log_exposure,
        e.SENSITO_LOG_EXPOSURE,
        e.SENSITO_DENSITY_RGB,
        e.SUBEMULSION_FAST_CENTRE_LOGE_RGB,
        e.SUBEMULSION_SPEED_OFFSETS_LOGE,
        e.SUBEMULSION_TRANSITION_WIDTH_RGB,
        e.SUBEMULSION_CAPACITY_FRACTIONS,
        e.SUBEMULSION_DYE_RECORD_MIX,
    )
    result["record_density_mix"] = {
        "numpy_seconds": record_numpy_seconds,
        "numba_seconds": record_numba_seconds,
        "speedup": record_numpy_seconds / record_numba_seconds,
        "error": error(record_reference, record_candidate),
    }
    del log_exposure, record_reference, record_candidate
    gc.collect()

    if not args.density.exists():
        mean_density = e.develop_5279_record_density(records)
        np.save(args.density, np.maximum(mean_density - e.SENSITO_DMIN_RGB, 0.0))
        del mean_density
        gc.collect()
    del film, records
    gc.collect()
    density = np.load(args.density, mmap_mode="r")
    lut = e.build_5279_net_density_lut()
    accel.density_cube_trilinear(
        np.asarray(density[:4, :4]), lut, e.NEGATIVE_5279_MAX_RECORD_DENSITY
    )
    e._NEGATIVE_5279_NET_DENSITY_LUT = lut
    density_reference, density_numpy_seconds = measure(
        e.apply_5279_net_density_lut, density
    )
    density_candidate, density_numba_seconds = measure(
        accel.density_cube_trilinear,
        density,
        lut,
        e.NEGATIVE_5279_MAX_RECORD_DENSITY,
    )
    result["density_cube"] = {
        "numpy_seconds": density_numpy_seconds,
        "numba_seconds": density_numba_seconds,
        "speedup": density_numpy_seconds / density_numba_seconds,
        "error": error(density_reference, density_candidate),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
