"""V64 published 2383 separated-curve density boundary.

H-61B requires a normally timed six-step print to appear neutral, but it does
not publish the six off-LAD Status-A triplets. The inherited density shaper
nonetheless changed the three vector-traced 2383 H-D curves by as much as
0.114 D toward an invented continuous principal-density mean. V64 withdraws
only that unmeasured curve rewrite. V63's actual 5279-to-2383 view-neutral
trajectory remains active and scan-referenced off-neutral colour stays frozen.
"""

from __future__ import annotations

import v63_profile


INPUT_CHROMA_RESIDUAL_D50 = v63_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v63_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v63_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v63_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v63_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v63_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v63_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v63_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v63_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v63_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v63_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v63_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v63_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v63_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY
PRINT_2383_DMIN_SPECTRAL_DENSITY = (
    v63_profile.PRINT_2383_DMIN_SPECTRAL_DENSITY
)
PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY = (
    v63_profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY
)
TRACE_SHA256 = v63_profile.TRACE_SHA256
STATUS_M_TABLE_SHA256 = v63_profile.STATUS_M_TABLE_SHA256
PRINT_2383_INTERIMAGE_MATRIX = v63_profile.PRINT_2383_INTERIMAGE_MATRIX.copy()
PRINT_2383_INTERIMAGE_POLICY = v63_profile.PRINT_2383_INTERIMAGE_POLICY
PRINT_2383_VIEW_NEUTRAL_POLICY = v63_profile.PRINT_2383_VIEW_NEUTRAL_POLICY


PRINT_2383_DENSITY_NEUTRAL_POLICY = (
    "published_separated_status_a_curves_unshaped_v64"
)


PROFILE = {
    **v63_profile.PROFILE,
    "name": "V64 · published 2383 separated H-D curves",
    "short_name": "V64",
    "version_id": "v64",
    "release_class": "evidence_withdrawn_unmeasured_2383_density_shaper",
    "image_change_from_v63": (
        "Withdraw the continuous principal-density mean shaper and retain the "
        "vector-traced Kodak separated-exposure Status-A H-D curves directly."
    ),
    "print_density_neutral_policy": PRINT_2383_DENSITY_NEUTRAL_POLICY,
    "projection_grain_observer_lattice_policy": "profile_identical_v64",
    "projection_colour_policy": "scan_referenced_v31",
    "evidence_boundary": (
        "H-61B's neutral six-patch requirement remains enforced at V63's "
        "actual modeled projection-view trajectory. No public source gives "
        "the six off-LAD 5279-to-2383 Status-A triplets required to rewrite "
        "the measured H-D curves in density space. Off-neutral physical colour "
        "and positive-film interimage remain unidentified and frozen."
    ),
}


def apply(module) -> None:
    v63_profile.apply(module)
    module.PRINT_2383_DENSITY_NEUTRAL_POLICY = (
        PRINT_2383_DENSITY_NEUTRAL_POLICY
    )
    module.refresh_5279_spectral_observer_caches()
