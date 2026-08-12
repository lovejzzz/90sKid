"""V60 registers V59's print-base spectrum to the H-D D-min coordinate.

V59 restored the spectral shape omitted from the 2383 dye graph, but treated
its graph-integrated Status-A density and the separately plotted H-D minima as
identical measurements. They differ by about 0.028 D in red and green. V60
keeps the official Visual Neutral residual as the projection spectrum while
defining zero analytical dye at each vector-traced H-D curve minimum. Thus the
spectral inverse operates on density above D-min and cannot ask a clear record
to have less absorption than the processed base.
"""

from __future__ import annotations

import v59_profile


INPUT_CHROMA_RESIDUAL_D50 = v59_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v59_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v59_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v59_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v59_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v59_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v59_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v59_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v59_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v59_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v59_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v59_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v59_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v59_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY
PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY = (
    v59_profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY
)
PRINT_2383_DMIN_SPECTRAL_DENSITY = (
    v59_profile.PRINT_2383_DMIN_SPECTRAL_DENSITY
)
TRACE_SHA256 = v59_profile.TRACE_SHA256


PROFILE = {
    **v59_profile.PROFILE,
    "name": "V60 · D-min-registered 2383 base spectrum",
    "short_name": "V60",
    "version_id": "v60",
    "release_class": "evidence_reconciled_2383_dmin_coordinate",
    "image_change_from_v59": (
        "Register V59's Visual Neutral residual spectrum to the independently "
        "vector-traced Status-A H-D minima, so zero dye amount maps exactly "
        "to each curve's D-min."
    ),
    "print_dmin_spectral_policy": (
        "vector_neutral_residual_dmin_registered_v60"
    ),
    "lad_coordinate_policy": "integral_spectral_inverse_v60",
    "evidence_boundary": (
        "The 2005 dye graph and H-D graph are representative rather than one "
        "batch's joint spectrophotometry. V60 preserves the former's spectral "
        "shape and the latter's per-channel density origin without inventing "
        "a wavelength-dependent correction to force the two drawings equal."
    ),
}


def apply(module) -> None:
    v59_profile.apply(module)
    module.PRINT_2383_DMIN_SPECTRAL_POLICY = (
        "vector_neutral_residual_dmin_registered_v60"
    )
    principal, amounts, residual = module.solve_2383_lad_principal_density_rgb(
        module.PRINT_2383_LAD_STATUS_A_AIM_RGB
    )
    module.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB = principal
    module.PRINT_2383_LAD_ANALYTICAL_AMOUNT_CMY = amounts
    module.PRINT_2383_LAD_INTEGRAL_RESIDUAL_RGB = residual
    module.PRINT_2383_LAD_PRINCIPAL_POLICY = "integral_spectral_inverse_v60"
    module.refresh_5279_spectral_observer_caches()
