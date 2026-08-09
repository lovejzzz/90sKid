"""V31 normal-process 2383 monitor colour adaptation.

V31 retains V30's official Kodak 2383 LAD channel aims and the accepted V29
5279 negative, grain, DIR, MTF, RAW-input and period-scan models.  It changes
only the Rec.709 presentation of the 2383 projection observer.  V30 preserved
OKLab C/L while applying a steeper neutral print-viewing curve; darker regions
therefore lost absolute chroma and combined with luma-dominant texture to read
like partial silver retention.  Normal ECN-2 and ECP-2D remove that silver.

The release adapter keeps the period-scan observer's low-frequency OKLab a/b,
the projection observer's high-frequency opponent residual, and the complete
projection luminance.  This is a colour/tone stage-order correction, not an
artistic saturation adjustment.  The profile-level absolute-chroma mode below
is retained as a documented placement probe; it was not the released V31 path.
"""

from __future__ import annotations

import v30_profile


PROFILE = {
    **v30_profile.PROFILE,
    "version_id": "v31",
    "short_name": "V31",
    "name": "V31 normal-process 2383 chroma-tone decoupling",
    "projection_chroma_adaptation": "absolute_chroma",
    "projection_chroma_crossover_sigma_at_2k": 0.72,
    "projection_change": (
        "retain V30 Kodak H-61B LAD and evidence-gated hue; preserve absolute "
        "scan-referenced OKLab chroma through the neutral 2383 lightness map "
        "instead of preserving C/L; at the final display boundary retain "
        "period-scan low-frequency dye colour and projection high-frequency "
        "opponent texture"
    ),
    "process_constraint": (
        "normal ECN-2 negative and ECP-2D print processing; no retained-silver, "
        "skip-bleach, ENR or bleach-bypass term"
    ),
    "film_constraint": (
        "V30/V29 5279 negative, grain, DIR, MTF, RAW input, scan observer, "
        "black, gamma, texture and Rec.709 delivery are unchanged"
    ),
}


def apply(module) -> None:
    v30_profile.apply(module)
    module.PRINT_MONITOR_CHROMA_ADAPTATION = PROFILE[
        "projection_chroma_adaptation"
    ]
    module._PRINT_2383_NEUTRAL_SHAPERS = None
    module._PRINT_2383_VIEW_NEUTRAL_TABLE = None
    module._PRINT_2383_H61_COLOUR_DELTA_LUTS = {}
    module._PRINT_2383_MONITOR_DELTA_LUT = None
    module._PRINT_2383_MONITOR_NEUTRAL_CURVE = None
    module._PRINT_2383_MONITOR_OUTPUT_LUT = None
