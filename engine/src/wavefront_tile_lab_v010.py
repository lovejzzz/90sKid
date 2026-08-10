"""Wavefront Tile Lab v0.1.0: five-class resident Metal emulsion island.

This remains an evidence-gated experiment.  One Metal command owns Philox
finite-site formation, disk integration, Gaussian optical spread, subpixel
phase, and weighted accumulation for all five size classes.  Only the completed
population deviation crosses back to the recovered NumPy engine.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

import numpy as np

import metal_emulsion_batch_bridge
import wavefront_tile_lab_v002


VERSION = "0.1.0"
STATS: dict[str, float | int | str] = {
    "version": VERSION,
    "backend": "Metal",
    "population_batches": 0,
    "size_classes": 0,
    "batch_seconds": 0.0,
}


def reset_stats() -> None:
    STATS.update(
        {
            "version": VERSION,
            "backend": "Metal",
            "population_batches": 0,
            "size_classes": 0,
            "batch_seconds": 0.0,
        }
    )
    for key in metal_emulsion_batch_bridge.STATS:
        metal_emulsion_batch_bridge.STATS[key] = 0


def population_optical_batch(
    module,
    probability: np.ndarray,
    rng: np.random.Generator,
    class_specs: Sequence[
        tuple[
            float,
            float,
            float,
            int,
            tuple[float, float],
            int,
        ]
    ],
) -> np.ndarray:
    """Form and sum one five-size-class population on one Metal command."""

    del rng
    if len(class_specs) != 5:
        raise ValueError("Wavefront v0.1.0 requires exactly five size classes")
    record_call = getattr(module, "_V35_RECORD_BINOMIAL_CALL", None)
    if record_call is None:
        raise RuntimeError("install the V35 Metal sampler before Wavefront v0.1.0")
    for spec in class_specs:
        record_call(int(spec[3]), int(spec[5]))
    started = time.perf_counter()
    result = metal_emulsion_batch_bridge.population(
        module,
        probability,
        class_specs,
        domain_salt=int(getattr(module, "_V35_METAL_DOMAIN_SALT", 0)),
    )
    STATS["population_batches"] = int(STATS["population_batches"]) + 1
    STATS["size_classes"] = int(STATS["size_classes"]) + len(class_specs)
    STATS["batch_seconds"] = (
        float(STATS["batch_seconds"]) + time.perf_counter() - started
    )
    return np.asarray(result, dtype=np.float32)


def install(module, *, marginal_tile_pixels: int = 250_000) -> None:
    """Install the resident Metal batch after the V35 Metal sampler."""

    if not hasattr(module, "_V35_RECORD_BINOMIAL_CALL"):
        raise RuntimeError("install the V35 Metal sampler before Wavefront v0.1.0")
    wavefront_tile_lab_v002.install(
        module,
        marginal_tile_pixels=int(marginal_tile_pixels),
    )
    reset_stats()

    def batch(probability, rng, class_specs):
        return population_optical_batch(
            module,
            probability,
            rng,
            class_specs,
        )

    module._WAVEFRONT_TILE_LAB_VERSION = VERSION
    module._WAVEFRONT_POPULATION_OPTICAL_BATCH = batch


def uninstall(module) -> None:
    if hasattr(module, "_WAVEFRONT_POPULATION_OPTICAL_BATCH"):
        delattr(module, "_WAVEFRONT_POPULATION_OPTICAL_BATCH")
    wavefront_tile_lab_v002.uninstall(module)


def snapshot() -> dict[str, object]:
    return dict(STATS) | {
        "metal_bridge": dict(metal_emulsion_batch_bridge.STATS),
        "v002": wavefront_tile_lab_v002.snapshot(),
    }
