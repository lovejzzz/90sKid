"""V36 comparison-integrity and 35 mm image-structure release.

V36 does not retune the accepted 5279 negative, MTF, grain morphology, colour,
tone or observer branches.  Its image model is V35.  The release fixes a
validation error: every scene must use the same absolute source-frame window as
the accepted V34 comparison.  This prevents source motion and scene content
from being misidentified as a change in temporal grain.

The release also records MTF and 48-micrometre diffuse RMS granularity as a
joint image-structure contract.  They remain separate measurements: density is
the image variable, while sharpness is the spatial transfer of density changes.
"""

from __future__ import annotations

import v35_profile


PROFILE = {
    **v35_profile.PROFILE,
    "name": "V36 · 5279 Baseline · matched-frame 35 mm structure",
    "short_name": "V36",
    "version_id": "v36",
    "image_change_from_v35": (
        "None. V36 corrects cross-version source-frame selection and adds a "
        "joint MTF/granularity validation contract; colour, tone, MTF, grain, "
        "DIR and both observers remain V35."
    ),
    "comparison_frame_contract": (
        "T002=0, T007=276 and T031=132; every comparison branch and version "
        "must use the same absolute source-frame index and frame count"
    ),
    "image_structure_contract": (
        "Kodak processed-stock R/G/B MTF and exposure-conditioned diffuse RMS "
        "granularity at a 48-micrometre aperture are validated jointly; "
        "absolute density is not itself sharpness"
    ),
    "pipeline_change": (
        "retain the validated V35 Production graph; lock curated absolute "
        "source-frame windows in release provenance and reject mismatched "
        "cross-version comparisons"
    ),
}


def apply(module) -> None:
    v35_profile.apply(module)
    module.GRAIN_SUBPIXEL_PHASE_MODE = "frame_random"
