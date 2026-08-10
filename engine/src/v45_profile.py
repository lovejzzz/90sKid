"""V45 official-observer spectral-integration profile."""

from __future__ import annotations

import v44_profile


INPUT_CHROMA_RESIDUAL_D50 = v44_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v44_profile.INPUT_CHROMA_RESIDUAL_STRENGTH


PROFILE = {
    **v44_profile.PROFILE,
    "name": "V45 · Official CIE Observer · 1 nm spectral integration",
    "short_name": "V45",
    "version_id": "v45",
    "release_class": "measured_observer_revision",
    "image_change_from_v44": (
        "Replace only the analytical 2383 observer's closed-form 20 nm CIE "
        "approximation with the official CIE 1931 2-degree 1 nm table and "
        "trapezoidal integration. All image-formation and delivery boundaries "
        "remain frozen at V44."
    ),
    "cie_observer": "CIE 1931 2 degree; official 1 nm table; 380--780 nm",
    "spectral_resampling": (
        "Kodak 2383 dye-density and xenon graph samples linearly interpolated "
        "from 20 nm to the official observer's 1 nm axis"
    ),
}


def apply(module) -> None:
    v44_profile.apply(module)
    module.PRINT_2383_CMF_MODE = "cie_1931_2deg_official_1nm"
    module._PRINT_2383_PROJECTION_LUT = None
    module._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    module._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    module._PRINT_2383_MONITOR_DELTA_LUT = None
    module._PRINT_2383_MONITOR_NEUTRAL_CURVE = None
    module._PRINT_2383_MONITOR_OUTPUT_LUT = None
