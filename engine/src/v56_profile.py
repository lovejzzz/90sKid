"""V56 physical 2383 colour-authority observer experiment.

V30 withdrew physical hue/saturation because its 2383 spectra were coarse and
wavelength-shifted. V31 consequently replaced the monitor projection's
low-frequency a/b with the period scan. V56 keeps V55 image formation and lets
the corrected spectral 2383 view own hue/chroma again. The accepted neutral
display curve and neutral-highlight guard remain, isolating colour authority.
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
    "name": "V56 · Physical 2383 colour authority experiment",
    "short_name": "V56",
    "version_id": "v56",
    "release_class": "evidence_enabled_observer_experiment",
    "image_change_from_v55": (
        "Stop replacing the vector-traced 2383 projection's low-frequency "
        "hue/chroma with the period scan after spectral integration."
    ),
    "projection_colour_policy": "physical_spectral_v56",
    "projection_lightness_policy": (
        "retain V55's neutral-derived Rec.709 display curve and neutral "
        "highlight guard; change colour authority only"
    ),
    "evidence_boundary": (
        "This is an observer experiment, not a measured theatre appearance "
        "transform. Official H-D, sensitivity, dye and CIE data now justify "
        "testing physical colour ownership, but the 2383 interimage matrix, "
        "xenon SPD, Callier term and display appearance transform remain "
        "partly inferred."
    ),
}


def apply(module) -> None:
    v55_profile.apply(module)
    module.PRINT_MONITOR_COLOUR_AUTHORITY = "physical_spectral_v56"
    module.refresh_5279_spectral_observer_caches()
