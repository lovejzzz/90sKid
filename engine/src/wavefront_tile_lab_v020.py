"""Wavefront Tile Lab v0.2.0: algebraically collapsed input residual.

The accepted V41 residual is a chain of linear colour transforms followed by
one scene-luminance restoration.  This lab composes the linear chain once and
evaluates it in one image pass.  It changes neither the fitted residual matrix
nor its neutral/luminance authority.  Wavefront v0.1.0 remains responsible for
the resident Metal emulsion population island.
"""

from __future__ import annotations

import time

import cv2
import numpy as np
from numba import njit, prange

import wavefront_tile_lab_v010


VERSION = "0.2.0"
STATS: dict[str, float | int | str] = {
    "version": VERSION,
    "residual_calls": 0,
    "residual_seconds": 0.0,
    "mean_dir_calls": 0,
    "mean_dir_seconds": 0.0,
}


@njit(parallel=True, cache=True)
def _apply_interimage_updates(
    diffused: np.ndarray,
    receiver_marginal: np.ndarray,
    scales: np.ndarray,
) -> np.ndarray:
    """Apply the separable DIR tensor in the historical source order."""

    height, width = diffused.shape[:2]
    correction = np.empty_like(diffused)
    for y in prange(height):
        for x in range(width):
            for destination_record in range(3):
                for destination_population in range(3):
                    value = np.float32(0.0)
                    marginal = receiver_marginal[
                        y, x, destination_record, destination_population
                    ]
                    for source_record in range(3):
                        for source_population in range(3):
                            value = np.float32(
                                value
                                - scales[
                                    destination_record,
                                    destination_population,
                                    source_record,
                                    source_population,
                                ]
                                * marginal
                                * diffused[
                                    y, x, source_record, source_population
                                ]
                            )
                    correction[
                        y, x, destination_record, destination_population
                    ] = value
    return correction


def _composite_input_residual(module) -> tuple[np.ndarray, np.ndarray]:
    """Compose the published V41 transform using column-vector notation."""

    strength = float(module.INPUT_CHROMA_RESIDUAL_STRENGTH)
    bt2020_to_xyz = np.asarray(module.BT2020_TO_XYZ_D65, dtype=np.float64)
    d65_to_d50 = np.asarray(module._BRADFORD_D65_TO_D50, dtype=np.float64)
    d50_to_d65 = np.asarray(module._BRADFORD_D50_TO_D65, dtype=np.float64)
    d50_white = np.asarray(module.D50_XYZ, dtype=np.float64)
    fitted = np.asarray(module.INPUT_CHROMA_RESIDUAL_D50, dtype=np.float64)

    y_selector = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    neutral_projector = np.outer(d50_white, y_selector)
    chroma_projector = np.eye(3, dtype=np.float64) - neutral_projector
    remove_y = np.eye(3, dtype=np.float64)
    remove_y[1, :] = 0.0
    residual = (1.0 - strength) * np.eye(3) + strength * fitted.T
    corrected_d50 = (
        neutral_projector
        + remove_y @ residual @ chroma_projector
    )
    composite = (
        np.linalg.inv(bt2020_to_xyz)
        @ d50_to_d65
        @ corrected_d50
        @ d65_to_d50
        @ bt2020_to_xyz
    )
    return (
        np.asarray(composite, dtype=np.float32),
        np.asarray(bt2020_to_xyz[1], dtype=np.float32),
    )


def apply_input_chroma_residual_collapsed(
    module,
    scene_linear: np.ndarray,
    composite: np.ndarray,
    d65_y: np.ndarray,
) -> np.ndarray:
    """Evaluate the accepted residual and its Y restoration in one pass."""

    source = np.asarray(scene_linear, dtype=np.float32)
    if (
        source.ndim != 3
        or source.shape[-1] != 3
        or not module.INPUT_CHROMA_RESIDUAL_ENABLED
        or module.INPUT_CHROMA_RESIDUAL_STRENGTH == 0.0
    ):
        return module._WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL(source)

    candidate = cv2.transform(source, composite)
    original_y = cv2.transform(source, d65_y.reshape(1, 3)).reshape(
        source.shape[:2]
    )
    corrected_y = cv2.transform(candidate, d65_y.reshape(1, 3)).reshape(
        source.shape[:2]
    )
    denominator = np.where(
        np.abs(corrected_y) > 1e-8,
        corrected_y,
        np.copysign(np.float32(1e-8), corrected_y + np.float32(1e-12)),
    )
    candidate *= (original_y / denominator)[..., None]
    return candidate.astype(np.float32, copy=False)


def reset_stats() -> None:
    STATS.update(
        {
            "version": VERSION,
            "residual_calls": 0,
            "residual_seconds": 0.0,
            "mean_dir_calls": 0,
            "mean_dir_seconds": 0.0,
        }
    )


def _dir_scales(module, layer_capacity: np.ndarray) -> np.ndarray:
    scales = np.zeros((3, 3, 3, 3), dtype=np.float32)
    for destination_record in range(3):
        for destination_population in range(3):
            for source_record in range(3):
                record_transport = module.DIR_INTERIMAGE_RECEIVER_CAUSER[
                    destination_record, source_record
                ]
                if record_transport <= 0.0:
                    continue
                for source_population in range(3):
                    scales[
                        destination_record,
                        destination_population,
                        source_record,
                        source_population,
                    ] = (
                        module.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH
                        * record_transport
                        * module.DIR_POPULATION_TRANSPORT[
                            destination_population, source_population
                        ]
                        * module.DIR_POPULATION_RELEASE_GAIN[source_population]
                        * module.DIR_POPULATION_RECEIVER_GAIN[
                            destination_population
                        ]
                        * layer_capacity[
                            destination_record, destination_population
                        ]
                    )
    return scales


def mean_dir_batch(
    module,
    release_departure: np.ndarray,
    receiver_marginal: np.ndarray,
    layer_capacity: np.ndarray,
    native_scale: float,
) -> np.ndarray:
    """Blur three record channels together, then fuse all DIR receivers."""

    departure = np.asarray(release_departure, dtype=np.float32)
    marginal = np.asarray(receiver_marginal, dtype=np.float32)
    if departure.ndim != 4 or departure.shape[-2:] != (3, 3):
        raise ValueError("mean DIR departure must be HxWx3x3")
    if marginal.shape != departure.shape:
        raise ValueError("mean DIR marginal must match departure")
    # OpenCV evaluates a multichannel Gaussian independently and bit-identically
    # to three scalar calls.  Reuse departure as the completed diffused tensor.
    for source_population in range(3):
        packed = np.ascontiguousarray(
            departure[..., :, source_population], dtype=np.float32
        )
        sigma = max(
            float(module.DIR_POPULATION_LATERAL_SIGMA_PX_5760[
                source_population
            ])
            * float(native_scale),
            0.20,
        )
        departure[..., :, source_population] = cv2.GaussianBlur(
            packed,
            (0, 0),
            sigma,
            borderType=cv2.BORDER_REFLECT,
        )
    return _apply_interimage_updates(
        departure,
        marginal,
        _dir_scales(module, layer_capacity),
    )


def install(module, *, marginal_tile_pixels: int = 250_000) -> None:
    """Install the lab after the accepted production engine is configured."""

    wavefront_tile_lab_v010.install(
        module,
        marginal_tile_pixels=int(marginal_tile_pixels),
    )
    if not hasattr(module, "_WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL"):
        module._WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL = (
            module.apply_input_chroma_residual
        )
    composite, d65_y = _composite_input_residual(module)
    reset_stats()

    def collapsed(scene_linear: np.ndarray) -> np.ndarray:
        started = time.perf_counter()
        result = apply_input_chroma_residual_collapsed(
            module,
            scene_linear,
            composite,
            d65_y,
        )
        STATS["residual_calls"] = int(STATS["residual_calls"]) + 1
        STATS["residual_seconds"] = (
            float(STATS["residual_seconds"]) + time.perf_counter() - started
        )
        return result

    def dir_batch(
        release_departure: np.ndarray,
        receiver_marginal: np.ndarray,
        layer_capacity: np.ndarray,
        native_scale: float,
    ) -> np.ndarray:
        started = time.perf_counter()
        result = mean_dir_batch(
            module,
            release_departure,
            receiver_marginal,
            layer_capacity,
            native_scale,
        )
        STATS["mean_dir_calls"] = int(STATS["mean_dir_calls"]) + 1
        STATS["mean_dir_seconds"] = (
            float(STATS["mean_dir_seconds"]) + time.perf_counter() - started
        )
        return result

    module._WAVEFRONT_TILE_LAB_VERSION = VERSION
    module.apply_input_chroma_residual = collapsed
    module._WAVEFRONT_MEAN_DIR_BATCH = dir_batch


def uninstall(module) -> None:
    reference = getattr(
        module,
        "_WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL",
        None,
    )
    if reference is not None:
        module.apply_input_chroma_residual = reference
        delattr(module, "_WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL")
    if hasattr(module, "_WAVEFRONT_MEAN_DIR_BATCH"):
        delattr(module, "_WAVEFRONT_MEAN_DIR_BATCH")
    wavefront_tile_lab_v010.uninstall(module)


def snapshot() -> dict[str, object]:
    return dict(STATS) | {"v010": wavefront_tile_lab_v010.snapshot()}
