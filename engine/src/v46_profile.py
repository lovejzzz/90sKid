"""V46 certified spectral inverse and stochastic endpoint correction.

V46 is the next public image release after V45.  It inherits the later
evidence audits consolidated in V72, then fixes two numerical defects that
those audits exposed: the nonnegative Status-M inverse is no longer a clipped
projected iteration, and the complete finite-site stochastic state is held at
the published granularity endpoints rather than extrapolated into an
unmeasured probability tail.
"""

from __future__ import annotations

import v72_profile


GRAIN_STOCHASTIC_EXPOSURE_POLICY = "full_stochastic_state_endpoint_hold"
NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY = (
    "adaptive_active_set_129_plus_5cube_v46"
)


PROFILE = {
    **v72_profile.PROFILE,
    "name": "V46 · Certified spectral inverse",
    "short_name": "V46",
    "version_id": "v46",
    "release_class": "certified_spectral_inverse_and_endpoint_correction",
    "image_change_from_v45": (
        "Consolidate the evidence-minimal V72 research baseline; replace the "
        "clipped Status-M inverse by a KKT-certified adaptive active-set "
        "observer; hold the complete stochastic state at Kodak's measured "
        "granularity endpoints."
    ),
    "grain_stochastic_exposure_policy": GRAIN_STOCHASTIC_EXPOSURE_POLICY,
    "negative_printer_density_observer_policy": (
        NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY
    ),
    "projection_grain_delta_lattice_policy": (
        "frozen_v66_defect_containment_boundary_v79"
    ),
    "evidence_boundary": (
        "The exact nonnegative inverse and endpoint policy correct numerical "
        "behaviour; they do not create unpublished Kodak measurements. The "
        "identity record-mix endpoint remains not a measurement, and V46 "
        "does not identify a particular Spirit scanner. "
        "adaptive microbrick cache is certified below 0.001 printer-density "
        "on synthetic stress points and sampled real negatives. V79's frozen "
        "projection grain-delta lattice remains an explicit defect-containment "
        "boundary because public data do not identify cross-record projection "
        "NPS; it is not represented as measured 5279/2383 physics."
    ),
}


def __getattr__(name: str):
    return getattr(v72_profile, name)


def apply(module) -> None:
    v72_profile.apply(module)
    module.GRAIN_STOCHASTIC_EXPOSURE_POLICY = (
        GRAIN_STOCHASTIC_EXPOSURE_POLICY
    )
    module.NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY = (
        NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY
    )
    module.refresh_5279_spectral_observer_caches()
