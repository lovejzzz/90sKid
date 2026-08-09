"""V32 measurement-first release contract.

V32 deliberately changes no image-forming parameter.  It freezes the accepted
V31 normal-process observer and adds independent scenes, cinema-monitor output,
temporal measurements and an OFX region-of-interest parity contract.
"""

from __future__ import annotations

import v31_profile


PROFILE = {
    **v31_profile.PROFILE,
    "version_id": "v32",
    "short_name": "V32",
    "name": "V32 measurement-first generalization and delivery contract",
    "image_change_from_v31": "none",
    "new_sources": {
        "T007": {"start_frame": 276, "frames": 24},
        "T031": {"start_frame": 132, "frames": 24},
    },
    "measurement_contract": (
        "native-format, luma-lock, neutral-axis stability, highlight endpoint, "
        "temporal stability, ST 428-1 DCDM round-trip and tiled-ROI parity gates"
    ),
    "cinema_reference": (
        "appearance-preserving SMPTE ST 428-1 12-bit X'Y'Z' DCDM TIFF test "
        "sequence; not a packaged DCP and not a new film look"
    ),
    "ofx_contract": (
        "float32 scene kernels, absolute source-frame seeds, host-scheduled "
        "frames and sigma-derived ROI halos"
    ),
}


def apply(module) -> None:
    v31_profile.apply(module)
