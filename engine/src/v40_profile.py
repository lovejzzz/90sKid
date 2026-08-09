"""V40 conservative colour-grain repair profile.

V39 correctly moved deterministic MTF and the realized negative into density
space, but it made three unsupported leaps: it treated Kodak's *post-process*
RMS observation as a pre-DIR source-layer target, let marginal record RMS
propagate to the final observer without the already validated high-frequency
opponent integration, and invented independent stochastic 2383 record
populations without stock-specific covariance or granularity data. V40 keeps
density as the image variable while returning every stochastic constraint to
the stage actually measured by the public data.
"""

from __future__ import annotations

import v39_profile


PROFILE = {
    **v39_profile.PROFILE,
    "name": "V40 · 5279 Baseline · conservative colour-grain repair",
    "short_name": "V40",
    "version_id": "v40",
    "image_change_from_v39": (
        "Constrain 5279 RMS at the published post-process density boundary; "
        "integrate the visible high-frequency opponent response in each "
        "observer; withdraw the unsupported independent per-record 2383 "
        "Poisson term; retain density-domain 5279/2383 MTF and physical RAW "
        "record "
        "formation, sensitometry, colour and delivery; prevent the final V31 "
        "adapter from reintroducing already-integrated high-frequency "
        "opponent colour. Withdraw the unmeasured signed intermediate "
        "film-basis cancellation used by V39."
    ),
    "negative_structure_domain": (
        "processed 5279 record density; observer-visible opponent response "
        "integrated after physical scan/print formation"
    ),
    "negative_granularity_calibration": (
        "Kodak diffuse 48-micrometre RMS constrains the processed 5279 "
        "record-density residual after stochastic DIR/interimage coupling; "
        "it is not inverted into unmeasured pre-DIR speed-layer yields"
    ),
    "print_structure_domain": (
        "2383 Status-A density with measured MTF; no unmeasured stochastic "
        "print-population term"
    ),
    "print_grain_model": (
        "5279 density structure transferred through 2383 MTF; intrinsic 2383 "
        "stochastic grain withheld until record covariance/NPS is measured"
    ),
    "v39_withdrawal_reason": (
        "a pre-DIR inverse model was not identified by Kodak's post-process "
        "RMS data, while marginal-RMS-only gates omitted visible colour "
        "covariance and extreme-tail tests, allowing primary-colour speckles"
    ),
    "projection_change": (
        "retain the accepted scan-referenced low-frequency dye colour and "
        "complete projection luminance; set the V31 adapter's unmeasured "
        "high-frequency opponent residual to zero after observer integration"
    ),
    "film_constraint": (
        "V30/V29 5279 sensitometry, mean colour, DIR/interimage transport, "
        "density-domain MTF, RAW input, black, gamma and exposure remain "
        "fixed; only unsupported stochastic inversions and duplicate "
        "high-frequency opponent passage are removed"
    ),
    # V24's 0.36 retention was calibrated after the older display-residual
    # graph. The nonlinear density observer turns the same unmeasured record
    # tail into isolated primaries. Do not pass an unidentified above-aperture
    # opponent remainder: the resolved low-frequency opponent field, broad
    # chromatic grain and all luma grain remain present.
    "projection_chroma_grain_high_frequency_retention": 0.0,
    "final_adapter_opponent_high_frequency_retention": 0.0,
    "projection_grain_luma_basis": "neutral Rec.709 luma axis",
    "projection_grain_delta_observer": (
        "accepted pointwise 5279-to-2383 observer for signed stochastic "
        "modulation only; analytical density observer owns deterministic mean"
    ),
    "projection_grain_delta_observer_id": "archive_pointwise",
    "raw_record_boundary": (
        "non-negative balanced film-light basis before record sensitivities; "
        "V39 signed intermediate cancellation withdrawn as underidentified"
    ),
}


def apply(module) -> None:
    v39_profile.apply(module)
    module.FILM_RGB_CLIP_BEFORE_RECORDS = True
    module.FILM_RECORD_BOUNDARY_MODE = "basis_clip"
    module.INPUT_CHROMA_RESIDUAL_ENABLED = False
    module.INPUT_CHROMA_RESIDUAL_STRENGTH = 0.0
    module.GRAIN_CALIBRATION_DOMAIN = "post_coupling_residual"
    module.FORMED_DENSITY_OBSERVER_GRAIN_MANAGEMENT = True
    module.PRINT_GRAIN_DOMAIN = "none"
    module.PROJECTION_GRAIN_DELTA_OBSERVER = "archive_pointwise"
    module.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION = PROFILE[
        "projection_chroma_grain_high_frequency_retention"
    ]
