"""V29 evidence-gated full-motion validation profile.

V29 retains the V28 image-forming parameters.  The public 5279 record constrains
neutral sensitometry, MTF and 48-micrometre diffuse RMS granularity, but does not
publish a stock-specific frequency-resolved grain spectrum, exact DIR transport
matrix, scanner spectral sensitivities or fast/medium/slow coating formula.
Those unidentified quantities are therefore not cosmetically tuned for V29.

The release implements the remaining validation work around the image model:
absolute frame-index stochastic seeds across independently rendered segments,
full-motion temporal checks, complete source duration, 24-bit production audio,
source timecode/metadata retention and explicit measurement manifests.
"""

from __future__ import annotations

import v28_profile


PROFILE = {
    **v28_profile.PROFILE,
    "version_id": "v29",
    "short_name": "V29",
    "name": "V29 evidence-gated full-motion 5279 validation",
    "negative_constraint": (
        "V28 5279 H-D, spectral dyes, DIR, MTF and exposure-conditioned "
        "48-micrometre RMS grain retained"
    ),
    "unidentified_parameter_policy": (
        "no change to NPS morphology, DIR coefficients, sub-emulsion recipe "
        "or period-scanner spectra without stock-specific measurement"
    ),
    "temporal_contract": (
        "every physical frame receives a new deterministic finite-site "
        "realization keyed by absolute source-frame index; segment boundaries "
        "cannot repeat or reset grain"
    ),
    "delivery_contract": (
        "native 5760x4320, complete source frame count, 12-bit ProRes 4444, "
        "Rec.709 1-1-1, source 24-bit/48-kHz four-channel PCM and timecode"
    ),
}


def apply(module) -> None:
    v28_profile.apply(module)
