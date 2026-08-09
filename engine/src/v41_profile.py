"""V41 chart-bounded colour transport profile.

V41 keeps V40's density formation, grain statistics, sensitometry, black,
gamma, observers and delivery contracts.  It changes only two input-colour
boundaries exposed by the T003 DKC-Pro control:

1. a cross-group, neutral/luminance-preserving chroma residual; and
2. signed intermediate basis transport only where all three 5279 record
   exposures remain physically non-negative.

The colour residual is deliberately recorded as provisional.  The chart's
published Lab values omit illuminant/observer metadata and the capture used
directional outdoor light, so V41 is an A/B research version rather than a
claim to recover Panasonic's or Kodak's proprietary characterization.
"""

from __future__ import annotations

import numpy as np

import v40_profile


# Average of two ridge fits (lambda=0.003): synthetic primaries -> natural
# colours and natural colours -> synthetic primaries.  Fitting and evaluation
# are performed on chroma deviations in Bradford-adapted D50 XYZ.  Averaging
# the disjoint-group fits prevents either row of the chart from becoming the
# sole authority.
INPUT_CHROMA_RESIDUAL_D50 = np.array(
    [
        [1.07541104, 0.0, 0.56043514],
        [0.0, 1.0, 0.0],
        [0.07077319, 0.0, 1.44047180],
    ],
    dtype=np.float32,
)

# The matrix is an error-direction estimate, not a camera characterization.
# T005 independently confirms the direction, but a full-strength application
# visibly over-corrects foliage and yellow patches after film formation.  Keep
# only the conservative one-eighth step that improves both disjoint chart rows on
# both clips.  A measured uniform-light target is required before increasing it.
INPUT_CHROMA_RESIDUAL_STRENGTH = 0.125


PROFILE = {
    **v40_profile.PROFILE,
    "name": "V41 · 5279 Baseline · chart-bounded colour transport",
    "short_name": "V41",
    "version_id": "v41",
    "image_change_from_v40": (
        "Apply a cross-group DKC-Pro chroma residual while preserving D65 "
        "neutral values, scene luminance and highlight headroom; replace the "
        "pre-record basis clip with record-positive signed transport only "
        "where every 5279 record exposure remains non-negative."
    ),
    "input_colour_residual": (
        "Bradford D65-to-D50 diagnostic basis; average of disjoint synthetic-"
        "primary and natural-colour ridge fits; lambda 0.003; 12.5% conservative "
        "step; chroma only; "
        "no white balance, exposure, gamma or artistic saturation control"
    ),
    "input_colour_authority": (
        "provisional T003 DKC-Pro A/B evidence; not a final GH7 camera profile "
        "until uniform measured D65/tungsten and orientation-bracket controls"
    ),
    "raw_record_boundary": (
        "retain signed BT.2020-to-film-basis values only when the combined "
        "5279 record exposures are all non-negative; otherwise use V40's "
        "non-negative basis fallback"
    ),
    "frozen_from_v40": (
        "5279 sensitometry, speed layers, DIR/interimage transport, processed "
        "48-micrometre RMS, density-domain MTF, observer grain integration, "
        "2383/Period-2K formation, black, gamma and 12-bit delivery"
    ),
    "fsd_contract": (
        "same deterministic V41 colour baseline; independent post-observer "
        "finite-site density only, N=176 and sigma=0.597 native pixels"
    ),
}


def apply(module) -> None:
    v40_profile.apply(module)
    module.FILM_RGB_CLIP_BEFORE_RECORDS = False
    module.FILM_RECORD_BOUNDARY_MODE = "record_positive_signed"
    module.INPUT_CHROMA_RESIDUAL_ENABLED = True
    module.INPUT_CHROMA_RESIDUAL_STRENGTH = INPUT_CHROMA_RESIDUAL_STRENGTH
    module.INPUT_CHROMA_RESIDUAL_D50 = INPUT_CHROMA_RESIDUAL_D50.copy()
