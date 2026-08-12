"""V58 integral-LAD coordinate correction.

V58 inherits V55 and changes one operation only.  Kodak H-61B's processed
2383 LAD aim is a simultaneous three-channel integral Status-A reading.  V30
through V57 incorrectly used those numbers as the principal densities of three
independent separation H-D curves.  V58 resolves the integral triplet through
the vector-traced formed-dye spectra, then uses the resulting separated-curve
principal densities to balance printer exposure and construct the neutral
shaper.  The empirical interimage and scan-referenced display observer remain
frozen so the coordinate correction can be evaluated independently.
"""

from __future__ import annotations

import v55_profile


INPUT_CHROMA_RESIDUAL_D50 = v55_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v55_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v55_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v55_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v55_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v55_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v55_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v55_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v55_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v55_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v55_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v55_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v55_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v55_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY


PROFILE = {
    **v55_profile.PROFILE,
    "name": "V58 · Integral Status-A LAD coordinate correction",
    "short_name": "V58",
    "version_id": "v58",
    "release_class": "evidence_corrected_2383_lad_coordinate",
    "image_change_from_v55": (
        "Resolve H-61B's simultaneous integral 1.09/1.06/1.03 Status-A LAD "
        "triplet into analytical dye amounts and separated-curve principal "
        "densities before inverting the three 2383 H-D curves."
    ),
    "projection_colour_policy": "scan_referenced_v31",
    "interimage_matrix_policy": "archive_cross_vendor_surrogate_unchanged",
    "lad_coordinate_policy": "integral_spectral_inverse_v58",
    "evidence_boundary": (
        "The coordinate conversion follows Kodak's distinction between "
        "integral and analytical density and uses only V55's official-vector "
        "2383 evidence. The public sheet does not publish a D-min spectrum, "
        "so measured per-channel curve minima remain additive Status-A terms. "
        "Interimage and the scan-referenced monitor observer are unchanged."
    ),
}


def apply(module) -> None:
    v55_profile.apply(module)
    principal, amounts, residual = module.solve_2383_lad_principal_density_rgb(
        module.PRINT_2383_LAD_STATUS_A_AIM_RGB
    )
    module.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB = principal
    module.PRINT_2383_LAD_ANALYTICAL_AMOUNT_CMY = amounts
    module.PRINT_2383_LAD_INTEGRAL_RESIDUAL_RGB = residual
    module.PRINT_2383_LAD_PRINCIPAL_POLICY = "integral_spectral_inverse_v58"
    module.refresh_5279_spectral_observer_caches()
