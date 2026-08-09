"""V42 research-conformant engine profile.

V42 is an engine and evidence-contract release, not a new colour grade or an
unsupported new Kodak measurement.  It preserves V41's accepted image model
while making the validated Production sampler, research invariants and
single-master delivery authority executable defaults.
"""

from __future__ import annotations

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
