"""V49 microscopic-density boundary candidate.

The published H-D endpoint is an aperture-averaged characteristic-curve value,
not a disclosed upper bound for every 4.3-micrometre native density sample.
V45/V48 nevertheless clamp each microscopic sample to macro D-max + 0.12,
creating an exact point mass in the high-exposure blue record. V49 removes only
that unmeasured upper guard. Total optical density remains non-negative and the
downstream spectral LUT retains its independently declared domain.
"""

from __future__ import annotations

import v48_profile


INPUT_CHROMA_RESIDUAL_D50 = v48_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v48_profile.INPUT_CHROMA_RESIDUAL_STRENGTH


PROFILE = {
    **v48_profile.PROFILE,
    "name": "V49 · Microscopic-density boundary candidate",
    "short_name": "V49",
    "version_id": "v49",
    "release_class": "microscopic_density_boundary_correction",
    "image_change_from_v48": (
        "Remove the exact point mass created when microscopic formed density "
        "is clamped to the representative macro H-D maximum plus 0.12. Keep "
        "non-negative optical density and every other V48 stage unchanged."
    ),
    "local_density_boundary": "nonnegative; no inferred macro-Dmax pixel clamp",
    "evidence_boundary": (
        "Kodak's representative characteristic-curve maximum and 48-micrometre "
        "RMS do not disclose a per-4.3-micrometre upper density distribution. "
        "V49 removes a demonstrated numerical pile-up but does not claim to "
        "measure the true microscopic coating-capacity tail."
    ),
}


def apply(module) -> None:
    v48_profile.apply(module)
    module.GRAIN_LOCAL_DENSITY_BOUND_MODE = "nonnegative_microscopic_density"
