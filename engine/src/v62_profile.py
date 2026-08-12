"""V62 evidence-separated 2383 interimage and observer-lattice correction.

V61 corrected the negative's Status-M/analytical coordinate while retaining a
3x3 positive-film interimage surrogate fitted years earlier to mixed finished
look transforms.  Those transforms are not same-process 5279/2383 chemical
measurements, and the corrected upstream coordinate makes their old inverse
fit structurally obsolete.  V62 therefore withdraws the surrogate from the
physical stage and exposes identity as an explicit *unmeasured* endpoint.

V62 also owns a newly generated 193-cube pointwise observer lattice.  V61's
production graph reused V60's lattice for microscopic grain deltas even though
its mean print used V61's corrected model.  The V62 lattice makes mean density
and density fluctuation pass through one version-identical observer.
"""

from __future__ import annotations

import numpy as np

import v61_profile


INPUT_CHROMA_RESIDUAL_D50 = v61_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v61_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v61_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v61_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v61_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v61_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v61_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v61_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v61_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v61_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v61_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v61_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v61_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v61_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY
PRINT_2383_DMIN_SPECTRAL_DENSITY = (
    v61_profile.PRINT_2383_DMIN_SPECTRAL_DENSITY
)
PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY = (
    v61_profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY
)
TRACE_SHA256 = v61_profile.TRACE_SHA256
STATUS_M_TABLE_SHA256 = v61_profile.STATUS_M_TABLE_SHA256


PRINT_2383_INTERIMAGE_MATRIX = np.eye(3, dtype=np.float32)
PRINT_2383_INTERIMAGE_POLICY = "unmeasured_identity_withheld_v62"


PROFILE = {
    **v61_profile.PROFILE,
    "name": "V62 · evidence-separated 2383 interimage and observer lattice",
    "short_name": "V62",
    "version_id": "v62",
    "release_class": "evidence_separated_2383_interimage_and_lattice",
    "image_change_from_v61": (
        "Withdraw the mixed-finished-look 3x3 surrogate from the physical "
        "2383 log-exposure stage and bind a V62-native 193-cube observer "
        "lattice so mean print density and microscopic density deltas use the "
        "same V62 model."
    ),
    "interimage_matrix_policy": PRINT_2383_INTERIMAGE_POLICY,
    "projection_grain_observer_lattice_policy": "profile_identical_v62",
    "evidence_boundary": (
        "Identity is not a measurement and does not assert that processed "
        "2383 has no chemical interimage effect. It is the least-parametric "
        "endpoint required when no same-process separated-exposure analytical-"
        "density set or DPX-to-theatre-Lab patch set is public. The archived "
        "matrix remains available only through historical profiles."
    ),
}


def apply(module) -> None:
    v61_profile.apply(module)
    module.PRINT_2383_INTERIMAGE_MATRIX = PRINT_2383_INTERIMAGE_MATRIX.copy()
    module.PRINT_2383_INTERIMAGE_POLICY = PRINT_2383_INTERIMAGE_POLICY
    module.refresh_5279_spectral_observer_caches()
