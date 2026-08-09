"""Explicit production-only float32 spatial kernels for V27/OFX research."""

from __future__ import annotations

import cv2
import numpy as np


def apply(module, *, residual_convolution: bool = False) -> None:
    """Install opt-in Production kernels; never used by Archive exact."""
    if not hasattr(module, "_V27_REFERENCE_ADD_5279_OPTICAL_SCATTER"):
        module._V27_REFERENCE_ADD_5279_OPTICAL_SCATTER = (
            module.add_5279_optical_scatter
        )
        module._V27_REFERENCE_FINISH_BLURAY_GRAIN_DELTA = (
            module.finish_bluray_grain_delta
        )

    if not hasattr(module, "_V27_REFERENCE_BINOMIAL_DYE_CLOUD_DEVIATION"):
        module._V27_REFERENCE_BINOMIAL_DYE_CLOUD_DEVIATION = (
            module.binomial_dye_cloud_deviation
        )

    def add_optical_scatter_float32(rec709: np.ndarray) -> np.ndarray:
        source_rgb = np.asarray(rec709, dtype=np.float32)
        luma = np.einsum(
            "...c,c->...",
            np.clip(source_rgb, 0.0, None),
            np.array([0.2126, 0.7152, 0.0722], dtype=np.float32),
        ).astype(np.float32)
        source = module.smoothstep(0.90, 3.5, luma).astype(np.float32)
        native_scale = source_rgb.shape[1] / 5760.0
        near = cv2.GaussianBlur(
            source, (0, 0), max(5.5 * native_scale, 0.1)
        )
        far = cv2.GaussianBlur(
            source, (0, 0), max(18.0 * native_scale, 0.1)
        )
        halo = 0.035 * near + 0.014 * far
        scatter_colour = np.array([1.0, 0.22, 0.045], dtype=np.float32)
        return (source_rgb + halo[..., None] * scatter_colour).astype(np.float32)

    def finish_bluray_grain_delta_float32(
        mean_linear: np.ndarray,
        grain_delta: np.ndarray,
    ) -> np.ndarray:
        mean = np.asarray(mean_linear, dtype=np.float32)
        delta = np.asarray(grain_delta, dtype=np.float32)
        weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        luma_delta = np.einsum("...c,c->...", delta, weights).astype(np.float32)
        opponent = (delta - luma_delta[..., None]).astype(np.float32)
        native_2k_scale = mean.shape[1] / 2048.0
        sigma = max(
            module.BLURAY_CHROMA_GRAIN_SIGMA_AT_2K * native_2k_scale,
            0.05,
        )
        opponent_low = cv2.GaussianBlur(
            opponent, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
        )
        opponent = (
            opponent_low
            + module.BLURAY_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION
            * (opponent - opponent_low)
        ).astype(np.float32)
        if module.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH != 1.0:
            opponent *= module.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH
        mean_luma = np.einsum(
            "...c,c->...", np.maximum(mean, 0.0), weights
        ).astype(np.float32)
        shadow_visibility = module.smoothstep(0.0012, 0.018, mean_luma).astype(
            np.float32
        )
        managed = luma_delta[..., None] + opponent
        return (managed * shadow_visibility[..., None]).astype(np.float32)

    module.add_5279_optical_scatter = add_optical_scatter_float32
    module.finish_bluray_grain_delta = finish_bluray_grain_delta_float32

    if residual_convolution:
        def binomial_dye_cloud_residual_convolution(
            activation_probability: np.ndarray,
            rng: np.random.Generator,
            radius: float,
            optical_sigma: float,
            site_count: int,
            subpixel_offset: tuple[float, float] = (0.0, 0.0),
            sample_seed: int | None = None,
        ) -> np.ndarray:
            """Apply the linear dye-cloud operator once to the sample residual.

            V27 applies the same normalized disk and Gaussian operators to the
            sampled fraction and its expectation, then subtracts the results.
            Production may reassociate this as L(sample - expectation), which
            halves those spatial filters but changes float32 rounding order.
            """
            probability = np.ascontiguousarray(
                activation_probability, dtype=np.float32
            )
            if module.BINOMIAL_SAMPLER_MODE == "striped_v25":
                if sample_seed is None:
                    raise ValueError(
                        "striped V25 sampler requires an explicit seed"
                    )
                residual = module._striped_binomial_sample(
                    probability, site_count, sample_seed
                )
            else:
                residual = rng.binomial(site_count, probability).astype(
                    np.float32
                )
            residual /= float(site_count)
            np.subtract(residual, probability, out=residual)

            kernel = module.disk_kernel(radius)
            kernel /= float(kernel.sum())
            deviation = cv2.filter2D(
                residual, -1, kernel, borderType=cv2.BORDER_REFLECT
            )
            deviation = cv2.GaussianBlur(
                deviation,
                (0, 0),
                max(optical_sigma, 0.05),
                borderType=cv2.BORDER_REFLECT,
            )
            offset_x, offset_y = subpixel_offset
            if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
                transform = np.array(
                    [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
                    dtype=np.float32,
                )
                deviation = cv2.warpAffine(
                    deviation,
                    transform,
                    (deviation.shape[1], deviation.shape[0]),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT,
                )
            return deviation.astype(np.float32, copy=False)

        module.binomial_dye_cloud_deviation = (
            binomial_dye_cloud_residual_convolution
        )
