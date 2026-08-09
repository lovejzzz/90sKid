"""Selected V24 35 mm texture profile.

This profile changes only stochastic morphology and the way visible opponent
grain is integrated by the projection/scan chain.  Mean colour, sensitometry,
MTF, highlight response, print exposure and scanner calibration remain V23.
"""

from __future__ import annotations

import numpy as np


PROFILE = {
    "name": "V24 35 mm spectral-separation texture",
    "negative_grain_correlation_scale": 0.76,
    "grain_size_class_fractions": [0.16, 0.30, 0.32, 0.17, 0.05],
    "grain_size_class_radius_factors": [0.50, 0.68, 0.86, 1.08, 1.34],
    "grain_size_class_optical_factors": [0.68, 0.80, 0.92, 1.05, 1.18],
    "projection_chroma_grain_sigma_at_2k": 0.62,
    "projection_chroma_grain_high_frequency_retention": 0.36,
    "projection_chroma_grain_opponent_strength": 0.66,
    "bluray_chroma_grain_sigma_at_2k": 0.72,
    "bluray_chroma_grain_high_frequency_retention": 0.30,
    "bluray_chroma_grain_opponent_strength": 0.64,
}


def apply(module) -> None:
    module.NEGATIVE_GRAIN_CORRELATION_SCALE = PROFILE["negative_grain_correlation_scale"]
    module.GRAIN_SIZE_CLASS_FRACTIONS = np.asarray(PROFILE["grain_size_class_fractions"], np.float32)
    module.GRAIN_SIZE_CLASS_RADIUS_FACTORS = np.asarray(PROFILE["grain_size_class_radius_factors"], np.float32)
    module.GRAIN_SIZE_CLASS_OPTICAL_FACTORS = np.asarray(PROFILE["grain_size_class_optical_factors"], np.float32)
    module.PROJECTION_CHROMA_GRAIN_SIGMA_AT_2K = PROFILE["projection_chroma_grain_sigma_at_2k"]
    module.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION = PROFILE["projection_chroma_grain_high_frequency_retention"]
    module.PROJECTION_CHROMA_GRAIN_OPPONENT_STRENGTH = PROFILE["projection_chroma_grain_opponent_strength"]
    module.BLURAY_CHROMA_GRAIN_SIGMA_AT_2K = PROFILE["bluray_chroma_grain_sigma_at_2k"]
    module.BLURAY_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION = PROFILE["bluray_chroma_grain_high_frequency_retention"]
    module.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH = PROFILE["bluray_chroma_grain_opponent_strength"]
