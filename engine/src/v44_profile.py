"""V44 observer-integrity and scale-honest review profile.

V44 is deliberately not another guessed 5279 noise-power spectrum.  Public
5279 evidence constrains diffuse RMS through a 48-micrometre aperture but does
not identify the stock's Wiener spectrum.  The accepted V42 negative therefore
remains unchanged.  This profile removes one hypothesis bundle and one
scale-ambiguous presentation path without inventing new emulsion measurements:

* an intrinsic 2383 stochastic term remains withheld; and
* the accepted V31 normal-process monitor boundary remains because the direct
  analytical projection colour fails the established native colour-tail gate.

Resolution-dependent review integration belongs to delivery, not to the
native-density master, and is recorded in profile metadata for the renderer.
"""

from __future__ import annotations

import v42_profile


INPUT_CHROMA_RESIDUAL_D50 = v42_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v42_profile.INPUT_CHROMA_RESIDUAL_STRENGTH


PROFILE = {
    **v42_profile.PROFILE,
    "name": "V44 · Observer Integrity · scale-honest review",
    "short_name": "V44",
    "version_id": "v44",
    "release_class": "evidence_boundary_revision",
    "image_change_from_v42": (
        "Keep the V42 5279 density formation, colour, tone and both physical "
        "observer models and accepted scan-referenced normal-process monitor "
        "boundary; keep intrinsic 2383 grain withheld and make display-scale "
        "review sampling explicit."
    ),
    "projection_colour_policy": "scan_referenced_v31",
    "review_sampling_policy": "linear_light_pixel_area_integration",
    "negative_nps_boundary": (
        "Kodak 48-micrometre diffuse RMS remains the amplitude authority; no "
        "public 5279-specific Wiener spectrum was recovered, so V44 does not "
        "claim a new intrinsic NPS or tune the master for appearance."
    ),
    "print_grain_boundary": (
        "No intrinsic 2383 stochastic term until record covariance and NPS "
        "are measured; transferred 5279 density structure remains."
    ),
    "observer_boundary": (
        "The analytical 2383 lightness/texture observer is retained, but its "
        "unvalidated direct colour fails native opponent-tail gates. The "
        "accepted V31 normal-process monitor boundary therefore supplies only "
        "low-frequency scan-referenced dye chroma; no new projection colour "
        "difference is invented without a measured print/projector reference."
    ),
}


def apply(module) -> None:
    v42_profile.apply(module)
    # Repeat the boundary explicitly so V43H -> V44 switching in a research
    # interpreter cannot retain the hypothesis-only print event.
    module.PRINT_GRAIN_DOMAIN = "none"
    module.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE = 0.0
    module.PRINT_2383_CMF_MODE = "analytic_20nm"
