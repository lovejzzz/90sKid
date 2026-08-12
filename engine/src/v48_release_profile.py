"""Public V48 first-principles projection-ownership release.

V46's negative, stochastic density, Kodak measurements, 2383 print and Cineon
scan are retained exactly.  V48 changes one downstream ownership boundary:
the deterministic projection colour is taken from the 5279 -> 2383 -> xenon /
CIE observer itself.  The historical scan-referenced publication transform is
retained only for the stochastic projection delta, where it remains an openly
declared safeguard for the unmeasured 5279 cross-record spectrum.

The executable profile key is ``v48r`` because the immutable laboratory archive
already contains an internal V48 numerical-integration experiment.  The public
visual release remains V48.
"""

from __future__ import annotations

import v46_profile


PROFILE = {
    **v46_profile.PROFILE,
    "name": "V48 · First-principles projection ownership",
    "short_name": "V48",
    "version_id": "v48r",
    "public_version_id": "v48",
    "release_class": "first_principles_projection_ownership",
    "image_change_from_v46": (
        "Keep the certified V46 negative and both material observers. Stop "
        "replacing deterministic 2383 hue/chroma with scan colour; retain the "
        "old containment transform only on the stochastic projection delta."
    ),
    "projection_colour_policy": "direct_mean_managed_grain_delta_v48",
    "projection_deterministic_colour_authority": (
        "5279_to_2383_xenon_cie_observer"
    ),
    "projection_stochastic_colour_policy": (
        "v46_scan_referenced_delta_containment_only"
    ),
    "evidence_boundary": (
        "V48 removes an observer-ownership substitution; it does not identify "
        "5279's unpublished cross-record NPS, exact DIR topology, a particular "
        "2383 batch, printer lamp, projector or theatre, and it does not "
        "identify a particular Spirit scanner. Identity record formation "
        "remains a minimum-assumption endpoint, not a measurement. The "
        "stochastic delta remains managed until calibrated 5279 cross-spectra "
        "exist."
    ),
}


def __getattr__(name: str):
    return getattr(v46_profile, name)


def apply(module) -> None:
    v46_profile.apply(module)
