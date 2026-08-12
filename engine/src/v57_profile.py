"""V57 minimal-interimage boundary experiment.

The public 2383 record does not identify an off-neutral 3x3 interimage matrix.
V56 exposes the Archive's cross-vendor empirical surrogate once scan colour is
removed. V57 changes only that matrix to identity, providing the minimum-
assumption endpoint of the remaining colour-identifiability interval.
"""

from __future__ import annotations

import numpy as np

import v56_profile


INPUT_CHROMA_RESIDUAL_D50 = v56_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v56_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v56_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v56_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v56_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v56_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v56_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v56_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v56_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v56_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v56_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v56_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v56_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v56_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY


PRINT_2383_INTERIMAGE_MATRIX = np.eye(3, dtype=np.float32)


PROFILE = {
    **v56_profile.PROFILE,
    "name": "V57 · Minimal 2383 interimage boundary experiment",
    "short_name": "V57",
    "version_id": "v57",
    "release_class": "unidentified_interimage_boundary_experiment",
    "image_change_from_v56": (
        "Replace only the unmeasured cross-vendor 2383 interimage surrogate "
        "with an identity matrix; retain physical spectral colour authority."
    ),
    "interimage_matrix_policy": "identity_minimum_assumption",
    "evidence_boundary": (
        "Identity is not a measurement and does not claim that real 2383 has "
        "no interimage effect. It is the least-parametric comparison endpoint "
        "until separated-exposure Status-A triplets or DPX-to-theatre Lab "
        "measurements identify the off-neutral matrix."
    ),
}


def apply(module) -> None:
    v56_profile.apply(module)
    module.PRINT_2383_INTERIMAGE_MATRIX = PRINT_2383_INTERIMAGE_MATRIX.copy()
    module.PRINT_2383_INTERIMAGE_POLICY = "identity_minimum_assumption_v57"
    module.refresh_5279_spectral_observer_caches()
