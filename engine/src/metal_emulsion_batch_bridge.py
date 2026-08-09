"""Resident Metal bridge for one five-size-class emulsion population."""

from __future__ import annotations

import ctypes
import subprocess
import time
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np


SOURCE = Path(__file__).with_suffix(".mm")
LIBRARY = Path("/tmp/libv43h_metal_emulsion_batch.dylib")
CLASS_COUNT = 5
MAX_DISK_COEFFICIENTS = 81
MAX_GAUSSIAN_COEFFICIENTS = 17
_FUNCTION = None
STATS: dict[str, float | int] = {
    "calls": 0,
    "bridge_seconds": 0.0,
    "wall_seconds": 0.0,
}


def load_bridge():
    global _FUNCTION
    if _FUNCTION is not None:
        return _FUNCTION
    if not LIBRARY.exists() or LIBRARY.stat().st_mtime < SOURCE.stat().st_mtime:
        subprocess.run(
            [
                "clang++",
                "-O3",
                "-dynamiclib",
                "-fobjc-arc",
                "-framework",
                "Foundation",
                "-framework",
                "Metal",
                str(SOURCE),
                "-o",
                str(LIBRARY),
            ],
            check=True,
        )
    library = ctypes.CDLL(str(LIBRARY))
    pointer_f32 = ctypes.POINTER(ctypes.c_float)
    pointer_u32 = ctypes.POINTER(ctypes.c_uint32)
    pointer_u64 = ctypes.POINTER(ctypes.c_uint64)
    function = library.metal_emulsion_population_f32
    function.argtypes = [
        pointer_f32,
        pointer_f32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        pointer_u32,
        pointer_u64,
        pointer_f32,
        pointer_f32,
        pointer_u32,
        pointer_f32,
        pointer_u32,
        pointer_f32,
    ]
    function.restype = ctypes.c_double
    _FUNCTION = function
    return function


def aligned_empty(shape, dtype=np.float32, page: int = 16_384) -> np.ndarray:
    target_dtype = np.dtype(dtype)
    count = int(np.prod(shape))
    owner = np.empty(count + page // target_dtype.itemsize, dtype=target_dtype)
    item_offset = ((-owner.ctypes.data) % page) // target_dtype.itemsize
    return owner[item_offset : item_offset + count].reshape(shape)


def _gaussian_coefficients(sigma: float) -> np.ndarray:
    size = int(np.rint(max(float(sigma), 0.05) * 8.0 + 1.0)) | 1
    if size > MAX_GAUSSIAN_COEFFICIENTS:
        raise ValueError(f"Gaussian kernel exceeds bridge capacity: {size}")
    return cv2.getGaussianKernel(
        size,
        max(float(sigma), 0.05),
        cv2.CV_32F,
    ).reshape(-1)


@lru_cache(maxsize=128)
def _opencv_effective_translation(
    offset_x: float, offset_y: float
) -> tuple[float, float]:
    """Measure OpenCV's fixed-point affine translation coefficients."""

    coordinates = np.arange(8, dtype=np.float32)
    ramp_x = np.broadcast_to(coordinates[None, :], (8, 8)).copy()
    ramp_y = np.broadcast_to(coordinates[:, None], (8, 8)).copy()
    transform = np.array(
        [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
        dtype=np.float32,
    )
    warped_x = cv2.warpAffine(
        ramp_x,
        transform,
        (8, 8),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    warped_y = cv2.warpAffine(
        ramp_y,
        transform,
        (8, 8),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    return 4.0 - float(warped_x[4, 4]), 4.0 - float(warped_y[4, 4])


def population(
    module,
    probability: np.ndarray,
    class_specs,
    *,
    domain_salt: int,
) -> np.ndarray:
    """Run Philox, optical integration, phase and accumulation in one command."""

    source = np.ascontiguousarray(probability, dtype=np.float32)
    if source.ndim != 2:
        raise ValueError("Metal emulsion input must be one scalar plane")
    if len(class_specs) != CLASS_COUNT:
        raise ValueError("Metal emulsion batch requires five size classes")
    trials = np.empty(CLASS_COUNT, dtype=np.uint32)
    seeds = np.empty(CLASS_COUNT, dtype=np.uint64)
    weights = np.empty(CLASS_COUNT, dtype=np.float32)
    offsets = np.empty(CLASS_COUNT * 2, dtype=np.float32)
    disk_sizes = np.empty(CLASS_COUNT, dtype=np.uint32)
    disk_coefficients = np.zeros(
        CLASS_COUNT * MAX_DISK_COEFFICIENTS,
        dtype=np.float32,
    )
    gaussian_sizes = np.empty(CLASS_COUNT, dtype=np.uint32)
    gaussian_coefficients = np.zeros(
        CLASS_COUNT * MAX_GAUSSIAN_COEFFICIENTS,
        dtype=np.float32,
    )
    for index, (
        class_weight,
        class_radius,
        class_sigma,
        class_sites,
        subpixel_offset,
        sample_seed,
    ) in enumerate(class_specs):
        trials[index] = int(class_sites)
        seeds[index] = (int(domain_salt) << 32) | (
            int(sample_seed) & 0xFFFFFFFF
        )
        weights[index] = float(class_weight)
        # OpenCV INTER_LINEAR combines a fixed-point affine setup with a
        # 1/32-pixel coefficient table.  Measure its effective pure translation
        # on coordinate ramps, then let Metal evaluate that same bilinear map.
        offsets[index * 2 : index * 2 + 2] = _opencv_effective_translation(
            float(subpixel_offset[0]),
            float(subpixel_offset[1]),
        )
        disk = np.asarray(
            module.disk_kernel(float(class_radius)), dtype=np.float32
        )
        disk /= float(disk.sum())
        if disk.size > MAX_DISK_COEFFICIENTS:
            raise ValueError(f"disk kernel exceeds bridge capacity: {disk.shape}")
        disk_sizes[index] = disk.shape[0]
        disk_start = index * MAX_DISK_COEFFICIENTS
        disk_coefficients[disk_start : disk_start + disk.size] = disk.reshape(-1)
        gaussian = _gaussian_coefficients(float(class_sigma))
        gaussian_sizes[index] = gaussian.size
        gaussian_start = index * MAX_GAUSSIAN_COEFFICIENTS
        gaussian_coefficients[
            gaussian_start : gaussian_start + gaussian.size
        ] = gaussian

    output = aligned_empty(source.shape)
    pointer_f32 = ctypes.POINTER(ctypes.c_float)
    pointer_u32 = ctypes.POINTER(ctypes.c_uint32)
    pointer_u64 = ctypes.POINTER(ctypes.c_uint64)
    started = time.perf_counter()
    bridge_seconds = load_bridge()(
        source.ctypes.data_as(pointer_f32),
        output.ctypes.data_as(pointer_f32),
        source.shape[1],
        source.shape[0],
        trials.ctypes.data_as(pointer_u32),
        seeds.ctypes.data_as(pointer_u64),
        weights.ctypes.data_as(pointer_f32),
        offsets.ctypes.data_as(pointer_f32),
        disk_sizes.ctypes.data_as(pointer_u32),
        disk_coefficients.ctypes.data_as(pointer_f32),
        gaussian_sizes.ctypes.data_as(pointer_u32),
        gaussian_coefficients.ctypes.data_as(pointer_f32),
    )
    wall_seconds = time.perf_counter() - started
    if bridge_seconds < 0.0:
        raise RuntimeError(f"Metal emulsion batch failed: {bridge_seconds}")
    STATS["calls"] = int(STATS["calls"]) + 1
    STATS["bridge_seconds"] = float(STATS["bridge_seconds"]) + bridge_seconds
    STATS["wall_seconds"] = float(STATS["wall_seconds"]) + wall_seconds
    return output
