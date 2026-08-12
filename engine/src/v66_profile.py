"""V66 Cineon printing-density coordinate correction.

Kodak defines Cineon data-scan code values as printing densities, not as raw
telecine RGB and not as three independent Status-M analytical records.  The
archive scanner model used broad period receivers, then moved them 82 percent
toward the independent record axes.  That is a useful unmeasured device prior,
but it is the wrong final coordinate for a Cineon data master.

V66 changes only this calibration target.  Formed 5279 density, multilayer
development, DIR, MTF, finite-site grain, the 2383 separated H-D curves, Cineon
0.002-D/code encoding and the existing display finishes remain unchanged.
Projection delivery changes downstream because its deliberately frozen
low-frequency colour authority is scan-referenced; V66 therefore owns a new
profile-identical projection-observer lattice as well.
"""

from __future__ import annotations

import v64_profile


INPUT_CHROMA_RESIDUAL_D50 = v64_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v64_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v64_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v64_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v64_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v64_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v64_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v64_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v64_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v64_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v64_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v64_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v64_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v64_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY
PRINT_2383_DMIN_SPECTRAL_DENSITY = (
    v64_profile.PRINT_2383_DMIN_SPECTRAL_DENSITY
)
PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY = (
    v64_profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY
)
TRACE_SHA256 = v64_profile.TRACE_SHA256
STATUS_M_TABLE_SHA256 = v64_profile.STATUS_M_TABLE_SHA256
PRINT_2383_INTERIMAGE_MATRIX = v64_profile.PRINT_2383_INTERIMAGE_MATRIX.copy()
PRINT_2383_INTERIMAGE_POLICY = v64_profile.PRINT_2383_INTERIMAGE_POLICY
PRINT_2383_VIEW_NEUTRAL_POLICY = v64_profile.PRINT_2383_VIEW_NEUTRAL_POLICY
PRINT_2383_DENSITY_NEUTRAL_POLICY = (
    v64_profile.PRINT_2383_DENSITY_NEUTRAL_POLICY
)


SPIRIT_PRIMARY_CORRECTION_TARGET = "active_2383_printing_density_v66"


PROFILE = {
    **v64_profile.PROFILE,
    "name": "V66 · Cineon printing-density coordinate",
    "short_name": "V66",
    "version_id": "v66",
    "release_class": "evidence_corrected_cineon_printing_density_coordinate",
    "image_change_from_v64": (
        "Replace the partial independent-Status-M scanner target with Kodak's "
        "printing-density coordinate before Cineon encoding."
    ),
    "spirit_primary_correction_target": SPIRIT_PRIMARY_CORRECTION_TARGET,
    "projection_grain_observer_lattice_policy": "profile_identical_v66",
    "projection_colour_policy": "scan_referenced_v31",
    "evidence_boundary": (
        "The Cineon printing-density meaning is standardized, but the exact "
        "Spirit xenon/filter/CCD response, proprietary primary correction and "
        "laboratory printer-lamp spectrum are not public measurements. V66 "
        "uses the active evidence-bounded 5279-to-2383 printer-density model "
        "as a coherent calibration target; it does not identify a particular "
        "Spirit serial number or a period Blu-ray grade."
    ),
}


def apply(module) -> None:
    v64_profile.apply(module)
    module.SPIRIT_PRIMARY_CORRECTION_TARGET = SPIRIT_PRIMARY_CORRECTION_TARGET
    module.refresh_5279_spectral_observer_caches()
