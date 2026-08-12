"""V72 evidence-minimal 5279 record-formation baseline.

V70/V71 showed that the speed-population source-to-destination record-mix
matrix has no independently identified observable, dominates the model's weak
cross-record grain covariance, and lowers colour-separation gamma before the
already modelled DIR and net-dye spectral observer.  V72 changes that one
operator to identity.  Every measured or previously accepted boundary remains
owned by V66.
"""

from __future__ import annotations

import numpy as np

import v66_profile


SUBEMULSION_DYE_RECORD_MIX = np.repeat(
    np.eye(3, dtype=np.float32)[None, ...], 3, axis=0
)


PROFILE = {
    **v66_profile.PROFILE,
    "name": "V72 · Evidence-minimal record formation",
    "short_name": "V72",
    "version_id": "v72",
    "release_class": "evidence_minimal_identity_record_formation",
    "image_change_from_v66": (
        "Withdraw the unmeasured direct fast/medium/slow source-to-destination "
        "record-mix prior to identity."
    ),
    "subemulsion_dye_record_mix_policy": "identity_v72",
    "projection_grain_observer_lattice_policy": "profile_identical_v66",
    "evidence_boundary": (
        "Identity is the minimum-assumption endpoint, not a measurement that "
        "real 5279 colour records are statistically independent. Kodak's net "
        "dye spectra, mask, spectral sensitivity and DIR remain active; their "
        "stock-specific separation/covariance coefficients are still not "
        "fully identified by public data. The inherited Cineon observer still "
        "does not identify a particular Spirit scanner."
    ),
}


def __getattr__(name: str):
    """Expose every frozen V66 authority not overridden by this candidate."""
    return getattr(v66_profile, name)


def apply(module) -> None:
    v66_profile.apply(module)
    module.SUBEMULSION_DYE_RECORD_MIX = SUBEMULSION_DYE_RECORD_MIX.copy()
