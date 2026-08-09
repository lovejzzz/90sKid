"""V33 camera-input and low-end delivery boundary contract.

V33 intentionally freezes the accepted V31/V32 image formation.  It separates
untouched as-shot exposure from the virtual film-EI offset and adds objective
black, toe, contrast, gamma, audio-range and native-raster release gates.
"""

from __future__ import annotations

import v32_profile


PROFILE = {
    **v32_profile.PROFILE,
    "version_id": "v33",
    "short_name": "V33",
    "name": "V33 camera-input and low-end boundary contract",
    "image_change_from_v32": "none",
    "default_input_mode": "as-shot metadata; no automatic tint neutralization",
    "diagnostic_input_mode": (
        "Technical Neutral is reserved and disabled until a measured gray-card "
        "or ColorChecker residual is repeatable across illuminants"
    ),
    "exposure_contract": {
        "as_shot_reference_stops": 0.0,
        "virtual_film_ei_stops": 0.45,
    },
    "low_end_contract": (
        "separate display-black clipping, toe occupancy, robust scene contrast "
        "and paired camera-to-observer effective gamma measurements"
    ),
    "fcp_witness_sha256": (
        "612077c7535122ea94fa752d470688e0f68bac0aaf18fa93a95b4bbf9761aa88"
    ),
    "native_raster": [5760, 4320],
    "partial_range_contract": (
        "frame-accurate PCM trim and source-frame-offset timecode; complete "
        "source renders retain stream-copy audio/timecode"
    ),
    "memory_safety_contract": (
        "native 5.7K float workers are capped from physical RAM; the 48-GiB "
        "reference machine selects one Archive-Exact worker and never trades "
        "image quality for scheduling speed"
    ),
}


def apply(module) -> None:
    v32_profile.apply(module)
