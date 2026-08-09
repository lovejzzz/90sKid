"""V30 evidence-corrected 2383 projection observer.

V30 changes only the print/projection branch.  The accepted V29 5279 negative,
grain, DIR, MTF, Panasonic RAW input contract and V27 period-scan observer are
unchanged.  Kodak H-61B's unequal 2383 Status-A LAD aims replace the former
equal-density assumption.  The Resolve D60 LUT is removed from the physical
default because it is a display-transform bracket rather than measured Kodak
chemistry.  A bounded physical-hue contribution acknowledges that the public
2383 dye graph and xenon plot are visually digitized, not spectral measurements.
"""

from __future__ import annotations

import numpy as np

import v29_profile


PROFILE = {
    **v29_profile.PROFILE,
    "version_id": "v30",
    "short_name": "V30",
    "name": "V30 evidence-corrected 2383 colour observer",
    "projection_lad_status_a_aim_rgb": [1.09, 1.06, 1.03],
    "projection_vendor_lut_strength": 0.0,
    "projection_physical_hue_weight": 0.00,
    "projection_physical_saturation_weight": 0.00,
    "projection_change": (
        "Kodak H-61B 2383 LAD aims; Resolve D60 LUT removed from physical "
        "observer; unmeasured digitized spectral hue excluded from the "
        "baseline in favour of the existing H-61/Spirit separation reference"
    ),
    "scan_constraint": "V29/V27 period 2K scan observer is unchanged",
    "film_constraint": (
        "V29/V28 5279 negative, grain, DIR, MTF, RAW input, scan observer, "
        "black, gamma and Rec.709 delivery are unchanged"
    ),
    "negative_constraint": (
        "V29/V28 5279 sensitometry, dyes, DIR, MTF and exposure-conditioned "
        "48-micrometre RMS grain are unchanged"
    ),
}


def apply(module) -> None:
    v29_profile.apply(module)
    module.PRINT_2383_LAD_STATUS_A_AIM_RGB = np.asarray(
        PROFILE["projection_lad_status_a_aim_rgb"], dtype=np.float32
    )
    module.PRINT_2383_D60_RELATIVE_CHROMA_STRENGTH = float(
        PROFILE["projection_vendor_lut_strength"]
    )
    module.PRINT_MONITOR_PHYSICAL_HUE_WEIGHT = float(
        PROFILE["projection_physical_hue_weight"]
    )
    module.PRINT_MONITOR_PHYSICAL_SATURATION_WEIGHT = float(
        PROFILE["projection_physical_saturation_weight"]
    )
    module._PRINT_2383_NEUTRAL_SHAPERS = None
    module._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    module._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    module._PRINT_2383_MONITOR_DELTA_LUT = None
    module._PRINT_2383_MONITOR_NEUTRAL_CURVE = None
    module._PRINT_2383_MONITOR_OUTPUT_LUT = None
