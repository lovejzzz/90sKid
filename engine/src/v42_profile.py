"""V42 research-conformant engine profile.

V42 is an engine and evidence-contract release, not a new colour grade or an
unsupported new Kodak measurement.  It preserves V41's accepted image model
while making the validated Production sampler, research invariants and
single-master delivery authority executable defaults.
"""

from __future__ import annotations

import numpy as np

import v41_profile


INPUT_CHROMA_RESIDUAL_D50 = v41_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v41_profile.INPUT_CHROMA_RESIDUAL_STRENGTH


PROFILE = {
    **v41_profile.PROFILE,
    "name": "V42 · 5279 Baseline · research-conformant engine",
    "short_name": "V42",
    "version_id": "v42",
    "image_change_from_v41": "None; accepted V41 image-formation parameters are frozen.",
    "engine_change_from_v41": (
        "Make the V35--V41 Philox-u32 Bernoulli Metal sampler the explicit "
        "Production default; retain Archive CPU as a reproducible reference; "
        "enforce V37--V41 image-model invariants at runtime; write one encoded "
        "12-bit BT.1886 picture authority and derive sRGB/stills from it."
    ),
    "release_boundary": (
        "V42 identifies executable research conformance. It does not claim a "
        "new 5279 sensitometric, spectral, DIR, MTF, grain or colour measurement."
    ),
}


def apply(module) -> None:
    v41_profile.apply(module)
    # Reset all later hypothesis-only observer state so V43H -> V42 switching
    # in a research interpreter cannot leak into the accepted baseline.
    module.SPIRIT_PERIOD_OBSERVER_CENTRES_NM = np.array(
        [620.0, 540.0, 470.0], dtype=np.float32
    )
    module.SPIRIT_PERIOD_OBSERVER_SIGMAS_NM = np.array(
        [52.0, 44.0, 38.0], dtype=np.float32
    )
    module._NEGATIVE_5279_NET_DENSITY_LUT = None
    module._SPIRIT_NEUTRAL_SCALE_TABLE = None
    module.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE = 0.0
    module.PRINT_2383_CMF_MODE = "analytic_20nm"
