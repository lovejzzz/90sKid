"""V63 actual neutral-trajectory observer-coordinate correction.

V58 corrected Kodak H-61B's LAD triplet from three separated H-D coordinates
to one simultaneous integral Status-A observation.  The projection observer,
however, still built its gray correction from equal principal Status-A
triplets inherited from V21.  That obsolete axis is not the neutral trajectory
formed by the current 5279 negative and 2383 print model.

V63 changes only the coordinate used to derive the view-neutral table.  It
traces neutral scene exposures through the complete V62 negative and print
path, then enforces H-61B's normal-process neutral-gray invariant at the view
boundary.  Scan-referenced colour authority remains frozen; this version does
not promote the still-unidentified physical off-neutral observer.
"""

from __future__ import annotations

import v62_profile


INPUT_CHROMA_RESIDUAL_D50 = v62_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v62_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v62_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v62_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v62_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v62_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v62_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v62_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v62_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v62_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v62_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v62_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v62_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v62_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY
PRINT_2383_DMIN_SPECTRAL_DENSITY = (
    v62_profile.PRINT_2383_DMIN_SPECTRAL_DENSITY
)
PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY = (
    v62_profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY
)
TRACE_SHA256 = v62_profile.TRACE_SHA256
STATUS_M_TABLE_SHA256 = v62_profile.STATUS_M_TABLE_SHA256
PRINT_2383_INTERIMAGE_MATRIX = v62_profile.PRINT_2383_INTERIMAGE_MATRIX.copy()
PRINT_2383_INTERIMAGE_POLICY = v62_profile.PRINT_2383_INTERIMAGE_POLICY


PRINT_2383_VIEW_NEUTRAL_POLICY = (
    "actual_5279_to_2383_neutral_trajectory_v63"
)


PROFILE = {
    **v62_profile.PROFILE,
    "name": "V63 · actual 5279-to-2383 neutral trajectory",
    "short_name": "V63",
    "version_id": "v63",
    "release_class": "evidence_corrected_projection_neutral_coordinate",
    "image_change_from_v62": (
        "Replace the obsolete equal-principal-Status-A projected-gray axis "
        "with the neutral trajectory formed by V62's complete 5279 negative "
        "and 2383 print model."
    ),
    "projection_view_neutral_policy": PRINT_2383_VIEW_NEUTRAL_POLICY,
    "projection_colour_policy": "scan_referenced_v31",
    "projection_grain_observer_lattice_policy": "profile_identical_v63",
    "evidence_boundary": (
        "H-61B directly requires a normally balanced six-step gray scale to "
        "appear neutral, but does not publish the six off-LAD Status-A "
        "triplets. V63 enforces that invariant along the model's actual "
        "neutral trajectory; it does not identify off-neutral 5279-to-2383 "
        "colour, chemical interimage coefficients or a theatre appearance "
        "transform. Physical hue/chroma authority therefore remains frozen."
    ),
}


def apply(module) -> None:
    v62_profile.apply(module)
    module.PRINT_2383_VIEW_NEUTRAL_POLICY = PRINT_2383_VIEW_NEUTRAL_POLICY
    # V34 accidentally inherited V30's label even though its documentation
    # declared the accepted V31 boundary.  Restore the declared configuration
    # for future introspection.  A V62 isolation showed that this switch is
    # numerically dormant under the current zero physical-colour weights.
    module.PRINT_MONITOR_CHROMA_ADAPTATION = "absolute_chroma"
    module.refresh_5279_spectral_observer_caches()
