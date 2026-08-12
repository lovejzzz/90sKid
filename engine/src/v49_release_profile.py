"""Public V49 conservative common-density stochastic release.

Kodak publishes the three 5279 Status-M marginal granularity curves, but not
their joint covariance or cross-power spectrum.  V49 therefore refuses to
turn the current independent-record realization into displayed RGB grain.
It retains only the scalar common-density component of that realization and
passes the resulting negative through the two material observers directly.

This is a conservative unidentified-joint-law boundary, not a measurement of
5279 cross-record registration.  The deterministic V48 colour and every
measured marginal input remain unchanged.
"""

from __future__ import annotations

import v48_release_profile


PROFILE = {
    **v48_release_profile.PROFILE,
    "name": "V49 · Conservative common-density formation",
    "short_name": "V49",
    "version_id": "v49r",
    "public_version_id": "v49",
    "release_class": "conservative_common_density_joint_law_boundary",
    "image_change_from_v48": (
        "Remove the display-RGB formed-minus-mean reinjection. Project the "
        "unidentified three-record stochastic residual onto one common optical-"
        "density field, form that density in the negative, and let 2383 and the "
        "scan observer see the same formed negative directly."
    ),
    "projection_colour_policy": "direct_observer",
    "negative_stochastic_publication_policy": (
        "symmetric_minimum_marginal_common_density_v49"
    ),
    "subemulsion_dye_record_mix_policy": "identity_v72",
    "projection_stochastic_colour_policy": "none_display_rgb",
    "evidence_boundary": (
        "Identity record formation remains not a measurement. V49 is not a "
        "claim that the three 5279 records have identical grain "
        "events. Kodak publishes marginal 48-micrometre RMS curves but not the "
        "cross-record covariance or cross-spectrum needed to identify coloured "
        "grain. A symmetric unit latent field scaled by the smallest local Kodak "
        "marginal is the conservative hypothesis: it cannot exceed any published "
        "record RMS. The common-density projection is the publishable "
        "component; discarded opponent density remains an uncertainty, not a "
        "creative denoise. Exact DIR topology, a particular 2383 batch, printer, "
        "projector and Spirit scanner also remain unidentified."
    ),
}


def __getattr__(name: str):
    return getattr(v48_release_profile, name)


def apply(module) -> None:
    v48_release_profile.apply(module)
    # No observer may rebuild the image as mean + display-RGB grain. The formed
    # common density is the image and passes through each material observer.
    module.FORMED_DENSITY_OBSERVER_GRAIN_MANAGEMENT = False
    module.PROJECTION_GRAIN_DELTA_OBSERVER = "formed_density"
