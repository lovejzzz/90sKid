"""V27 density-dependent period-scan neutral-scale calibration.

V26 remains the negative, projection, grain and output baseline.  V27 changes
only the finished Cineon/Blu-ray observer: a measured internal neutral step
scale replaces the former two-anchor assumption while preserving each pixel's
existing Rec.709 luminance exactly.

The latest hourly research is applied as an evidence boundary.  It found no
published 5279 NPS, DIR/interimage coefficient or stock-specific JVT grain
payload, so none of those bounded morphology parameters changes in V27.
"""

from __future__ import annotations

import v26_profile


PROFILE = {
    **v26_profile.PROFILE,
    "name": "V27 neutral-scale constrained period 2K scan",
    "scan_change": "density-dependent neutral-scale calibration after the period 2K observer",
    "luminance_constraint": "per-pixel Rec.709 luminance preserved exactly before output encoding",
    "projection_constraint": "V26 projection branch unchanged",
    "hourly_research_boundary": (
        "no grain, DIR or NPS parameter change without stock-specific, "
        "frequency-resolved or separation-wedge evidence"
    ),
}


def apply(module) -> None:
    v26_profile.apply(module)
    module.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED = True
    module._SPIRIT_NEUTRAL_SCALE_TABLE = None
