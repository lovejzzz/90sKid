"""V28 colour-input contract for AVFoundation-decoded ProRes RAW.

V27 remains the negative, grain, DIR, Spirit observer and delivery baseline.
V28 corrects one stage-order error: AVFoundation's requested float buffer is
already extended-linear BT.2020/D65, so it must be converted by primaries rather
than passed through Panasonic's RAW-Gamut camera LUT a second time.
"""

from __future__ import annotations

import numpy as np

import v27_profile


PROFILE = {
    **v27_profile.PROFILE,
    "version_id": "v28",
    "short_name": "V28",
    "name": "V28 AVFoundation linear-BT.2020 input contract",
    "raw_colour": "avfoundation_bt2020",
    "input_decode": "Apple extended-linear BT.2020 RGB float32 / D65",
    "raw_colour_transform": (
        "linear BT.2020 -> XYZ D65 -> Panasonic V-Gamut; no RAW-Gamut LUT"
    ),
    "white_balance_contract": (
        "retain AVFoundation standard ProRes RAW conversion/as-shot metadata; "
        "do not apply a second creative or chromatic white balance"
    ),
    "camera_lut_boundary": (
        "Panasonic VLog_RAWGamut_to_VLog_VGamut is valid only when the decoder "
        "supplies Panasonic RAW Gamut at the documented Camera-LUT stage"
    ),
    "film_constraint": (
        "V27 sensitometry, dye spectra, DIR, grain, Spirit, black, gamma and "
        "output encoding unchanged"
    ),
}


def apply(module) -> None:
    v27_profile.apply(module)
    # Restore pre-V34 input/MTF operation order when multiple profiles are
    # evaluated in one interpreter (validation tools do this deliberately).
    module.AVFOUNDATION_DIRECT_FILM_MATRIX_ENABLED = False
    module.DIR_DETERMINISTIC_INTRALAYER_STRENGTH_RGB = (
        module.DIR_DEVELOPMENT_INTRALAYER_STRENGTH_RGB.copy()
    )
    # Restore the archived V28/V29 print observer when profiles are switched in
    # one Python process.  V30 deliberately overrides these after applying V29.
    module.PRINT_2383_LAD_STATUS_A_AIM_RGB = np.full(
        3, module.PRINT_2383_LAD_DENSITY, dtype=np.float32
    )
    module.PRINT_2383_D60_RELATIVE_CHROMA_STRENGTH = 1.0
    module.PRINT_MONITOR_PHYSICAL_HUE_WEIGHT = 1.0
    module.PRINT_MONITOR_PHYSICAL_SATURATION_WEIGHT = 0.60
    module.PRINT_MONITOR_CHROMA_ADAPTATION = "relative_saturation"
