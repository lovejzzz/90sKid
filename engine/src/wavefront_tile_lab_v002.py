"""Wavefront Tile Lab v0.0.2: exact optical-buffer contraction."""

from __future__ import annotations

import time

import cv2
import numpy as np

import wavefront_tile_lab_v001


VERSION = "0.0.2"
STATS: dict[str, float | int | str] = {
    "version": VERSION,
    "optical_calls": 0,
    "optical_seconds": 0.0,
    "class_accumulation_calls": 0,
    "class_accumulation_seconds": 0.0,
}


def reset_stats() -> None:
    STATS.update(
        {
            "version": VERSION,
            "optical_calls": 0,
            "optical_seconds": 0.0,
            "class_accumulation_calls": 0,
            "class_accumulation_seconds": 0.0,
        }
    )


def optical_deviation_inplace(
    developed_fraction: np.ndarray,
    expected: np.ndarray,
    kernel: np.ndarray,
    sigma: float,
    subpixel_offset: tuple[float, float],
) -> np.ndarray:
    """Run accepted disk/Gaussian/subtract/warp order in two reused planes."""

    sampled = np.asarray(developed_fraction)
    mean = np.asarray(expected)
    if (
        sampled.dtype != np.float32
        or mean.dtype != np.float32
        or sampled.ndim != 2
        or sampled.shape != mean.shape
        or not sampled.flags.writeable
        or not mean.flags.writeable
    ):
        raise ValueError("optical buffers must be matching writeable float32 planes")
    started = time.perf_counter()
    sampled = cv2.filter2D(
        sampled,
        -1,
        kernel,
        dst=sampled,
        borderType=cv2.BORDER_REFLECT,
    )
    sampled = cv2.GaussianBlur(
        sampled,
        (0, 0),
        max(float(sigma), 0.05),
        dst=sampled,
        borderType=cv2.BORDER_REFLECT,
    )
    mean = cv2.GaussianBlur(
        mean,
        (0, 0),
        max(float(sigma), 0.05),
        dst=mean,
        borderType=cv2.BORDER_REFLECT,
    )
    np.subtract(sampled, mean, out=sampled)
    offset_x, offset_y = subpixel_offset
    if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
        transform = np.array(
            [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
            dtype=np.float32,
        )
        sampled = cv2.warpAffine(
            sampled,
            transform,
            (sampled.shape[1], sampled.shape[0]),
            dst=sampled,
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT,
        )
    STATS["optical_calls"] = int(STATS["optical_calls"]) + 1
    STATS["optical_seconds"] = (
        float(STATS["optical_seconds"]) + time.perf_counter() - started
    )
    return sampled


def weight_and_accumulate_class(
    population_deviation: np.ndarray,
    class_deviation: np.ndarray,
    class_weight: float,
) -> None:
    """Consume a finished class plane as its weighted accumulation scratch."""

    population = np.asarray(population_deviation)
    deviation = np.asarray(class_deviation)
    if (
        population.dtype != np.float32
        or deviation.dtype != np.float32
        or population.shape != deviation.shape
        or not population.flags.writeable
        or not deviation.flags.writeable
    ):
        raise ValueError("class buffers must be matching writeable float32 planes")
    started = time.perf_counter()
    np.multiply(deviation, float(class_weight), out=deviation)
    np.add(population, deviation, out=population)
    STATS["class_accumulation_calls"] = (
        int(STATS["class_accumulation_calls"]) + 1
    )
    STATS["class_accumulation_seconds"] = (
        float(STATS["class_accumulation_seconds"])
        + time.perf_counter()
        - started
    )


def install(module, *, marginal_tile_pixels: int = 250_000) -> None:
    """Enable v0.0.1 plus v0.0.2's opt-in lifetime contractions."""

    wavefront_tile_lab_v001.install(
        module, tile_pixels=int(marginal_tile_pixels)
    )
    reset_stats()
    module._WAVEFRONT_TILE_LAB_VERSION = VERSION
    module._WAVEFRONT_INPLACE_OPTICAL_BUFFERS = True
    module._WAVEFRONT_INPLACE_CLASS_ACCUMULATION = True


def uninstall(module) -> None:
    for name in (
        "_WAVEFRONT_INPLACE_OPTICAL_BUFFERS",
        "_WAVEFRONT_INPLACE_CLASS_ACCUMULATION",
    ):
        if hasattr(module, name):
            delattr(module, name)
    wavefront_tile_lab_v001.uninstall(module)


def snapshot() -> dict[str, object]:
    return dict(STATS) | {"v001": wavefront_tile_lab_v001.snapshot()}
