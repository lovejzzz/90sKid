"""Wavefront Tile Lab v0.0.1: exact activation-lifetime contraction.

This lab does not change the V43H image model or default scheduler. It replaces
one full nine-plane DIR marginal allocation with an exact in-place, row-tiled
transition after activation probabilities have reached their final consumer.
"""

from __future__ import annotations

import time

import numpy as np


VERSION = "0.0.1"
STATS: dict[str, float | int | str] = {
    "version": VERSION,
    "calls": 0,
    "seconds": 0.0,
    "requested_tile_pixels": 0,
    "maximum_tile_pixels": 0,
    "maximum_scratch_bytes": 0,
}


def reset_stats() -> None:
    STATS.update(
        {
            "version": VERSION,
            "calls": 0,
            "seconds": 0.0,
            "requested_tile_pixels": 0,
            "maximum_tile_pixels": 0,
            "maximum_scratch_bytes": 0,
        }
    )


def activation_marginal_inplace(
    activations: np.ndarray,
    *,
    tile_pixels: int,
) -> np.ndarray:
    """Compute clip(4*a*(1-a), 0, 1) in place, preserving float32 order."""

    field = np.asarray(activations)
    if field.dtype != np.float32 or field.ndim != 4 or field.shape[-2:] != (3, 3):
        raise ValueError("activation field must be H x W x 3 x 3 float32")
    if not field.flags.writeable:
        raise ValueError("activation field must be writeable")
    if tile_pixels < 1:
        raise ValueError("tile pixels must be positive")

    height, width = field.shape[:2]
    rows = max(1, int(tile_pixels) // width)
    started = time.perf_counter()
    scratch = np.empty(
        (min(rows, height), width, 3, 3), dtype=np.float32
    )
    maximum_pixels = 0
    for row0 in range(0, height, rows):
        row1 = min(row0 + rows, height)
        tile = field[row0:row1]
        complement = scratch[: row1 - row0]
        # This is the exact ufunc order of the accepted expression:
        # 4.0 * activations * (1.0 - activations), followed by clip.
        np.subtract(1.0, tile, out=complement)
        np.multiply(tile, 4.0, out=tile)
        np.multiply(tile, complement, out=tile)
        np.clip(tile, 0.0, 1.0, out=tile)
        maximum_pixels = max(maximum_pixels, (row1 - row0) * width)

    STATS["calls"] = int(STATS["calls"]) + 1
    STATS["seconds"] = float(STATS["seconds"]) + time.perf_counter() - started
    STATS["requested_tile_pixels"] = int(tile_pixels)
    STATS["maximum_tile_pixels"] = max(
        int(STATS["maximum_tile_pixels"]), maximum_pixels
    )
    STATS["maximum_scratch_bytes"] = max(
        int(STATS["maximum_scratch_bytes"]), scratch.nbytes
    )
    return field


def install(module, *, tile_pixels: int = 1_000_000) -> None:
    """Enable the isolated v0.0.1 lifetime experiment on a configured graph."""

    if tile_pixels < 1:
        raise ValueError("tile pixels must be positive")
    reset_stats()
    module._WAVEFRONT_TILE_LAB_VERSION = VERSION
    module._WAVEFRONT_INPLACE_MARGINAL_TILE_PIXELS = int(tile_pixels)


def uninstall(module) -> None:
    """Remove only v0.0.1's opt-in flags; the configured engine stays intact."""

    for name in (
        "_WAVEFRONT_TILE_LAB_VERSION",
        "_WAVEFRONT_INPLACE_MARGINAL_TILE_PIXELS",
    ):
        if hasattr(module, name):
            delattr(module, name)


def snapshot() -> dict[str, float | int | str]:
    return dict(STATS)
