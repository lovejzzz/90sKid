"""V38 reference-display delivery correction.

The V37 negative, print, scan and temporal grain model remain frozen.  V38
changes only the encoding after the observers have produced display-linear
Rec.709 light.  The archival master is encoded for an ideal-zero-black
BT.1886 reference display; a separate sRGB-tagged ProRes companion is provided
for colour-managed QuickTime and desktop review.
"""

from __future__ import annotations

import v37_profile


PROFILE = {
    **v37_profile.PROFILE,
    "name": "V38 · 5279 Baseline · reference-display delivery",
    "short_name": "V38",
    "version_id": "v38",
    "image_change_from_v37": "None; the display-linear observer image is frozen.",
    "delivery_family": "display_linear_dual_encoding",
    "reference_master_encoding": (
        "inverse BT.1886 ideal-zero-black gamma 2.4; Rec.709 primaries/matrix; "
        "12-bit ProRes 4444; 1-1-1 interchange signalling"
    ),
    "quicktime_companion_encoding": (
        "IEC 61966-2-1 sRGB transfer; Rec.709 primaries/matrix; 12-bit ProRes "
        "4444; authoritative MOV 1-13-1 colour atom"
    ),
    "delivery_change": (
        "replace the duplicated camera-OETF/system-gamma boundary with two "
        "explicit encodings of the same display-linear observer light"
    ),
    "delivery_consistency_contract": (
        "stills and web media derive from the sRGB companion; professional "
        "master and QuickTime companion decode to the same display-linear RGB"
    ),
}


def apply(module) -> None:
    v37_profile.apply(module)
    # Explicit Archive reset keeps profile switching deterministic in one
    # interpreter after a V39 experiment has been selected.
    module.FILM_RGB_CLIP_BEFORE_RECORDS = True
    module.GRAIN_CALIBRATION_DOMAIN = "post_coupling_residual"
    module.IMAGE_STRUCTURE_DOMAIN = "display_residual"
    module.PRINT_GRAIN_DOMAIN = "display_ratio"
    module.FORMED_DENSITY_OBSERVER_GRAIN_MANAGEMENT = False
    module.PROJECTION_GRAIN_DELTA_OBSERVER = "formed_density"
