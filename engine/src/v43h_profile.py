"""V43H Hypothesis Edition.

This profile is intentionally not the measured V42 baseline.  It supplies
central, falsifiable estimates only where the existing primary-source record
bounds a missing variable's direction or family.  Every hypothesis is isolated
here so a future 5279/2383/Spirit measurement can replace it without rewriting
the accepted engine.
"""

from __future__ import annotations

import numpy as np

import v42_profile


INPUT_CHROMA_RESIDUAL_D50 = v42_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v42_profile.INPUT_CHROMA_RESIDUAL_STRENGTH


# A conservative 25% shrinkage step from V21's broad generic telecine family
# toward the lowest-error *synthetic* Spirit sweep candidate.  The candidate
# landed on the sweep boundary, so a full substitution is not justified.
SPIRIT_BASE_CENTRES_NM = np.array([620.0, 540.0, 470.0], dtype=np.float32)
SPIRIT_CANDIDATE_CENTRES_NM = np.array([630.0, 550.0, 460.0], dtype=np.float32)
SPIRIT_BASE_SIGMAS_NM = np.array([52.0, 44.0, 38.0], dtype=np.float32)
SPIRIT_CANDIDATE_SIGMAS_NM = 0.8 * SPIRIT_BASE_SIGMAS_NM
SPIRIT_HYPOTHESIS_WEIGHT = np.float32(0.25)
SPIRIT_PERIOD_OBSERVER_CENTRES_NM = (
    SPIRIT_BASE_CENTRES_NM
    + SPIRIT_HYPOTHESIS_WEIGHT
    * (SPIRIT_CANDIDATE_CENTRES_NM - SPIRIT_BASE_CENTRES_NM)
).astype(np.float32)
SPIRIT_PERIOD_OBSERVER_SIGMAS_NM = (
    SPIRIT_BASE_SIGMAS_NM
    + SPIRIT_HYPOTHESIS_WEIGHT
    * (SPIRIT_CANDIDATE_SIGMAS_NM - SPIRIT_BASE_SIGMAS_NM)
).astype(np.float32)


PROFILE = {
    **v42_profile.PROFILE,
    "name": "V43H · Hypothesis Edition · bounded missing physics",
    "short_name": "V43H",
    "version_id": "v43h",
    "release_class": "hypothesis_not_measurement",
    "question": (
        "If the most likely but still unmeasured parts of the existing 5279 "
        "research are completed with bounded central estimates, what might "
        "the stock look like?"
    ),
    "image_change_from_v42": (
        "Use a finer, narrower-tailed five-node 35 mm dye-cloud morphology "
        "while retaining Kodak's exposure-conditioned 48-micrometre RMS; "
        "move the provisional Spirit spectral observer 25% toward the best "
        "bounded synthetic candidate; add a very weak, fully common-mode "
        "2383 Status-A density event to projection only."
    ),
    "negative_nps_hypothesis": {
        "correlation_scale": 0.72,
        "radius_factors": [0.46, 0.64, 0.83, 1.04, 1.30],
        "optical_factors": [0.72, 0.83, 0.94, 1.06, 1.18],
        "population_fractions": [
            [0.10, 0.25, 0.36, 0.22, 0.07],
            [0.17, 0.32, 0.32, 0.15, 0.04],
            [0.26, 0.36, 0.27, 0.09, 0.02],
        ],
        "amplitude_authority": (
            "unchanged Kodak 5279 per-record diffuse RMS at 48 micrometres"
        ),
    },
    "spirit_hypothesis": {
        "weight_toward_synthetic_candidate": 0.25,
        "centres_nm": SPIRIT_PERIOD_OBSERVER_CENTRES_NM.tolist(),
        "sigmas_nm": SPIRIT_PERIOD_OBSERVER_SIGMAS_NM.tolist(),
        "boundary": (
            "generic Kodak telecine plot plus DFT Spirit architecture; not "
            "measured Spirit dichroic/CCD curves"
        ),
    },
    "print_grain_hypothesis": {
        "domain": "2383 Status-A density",
        "record_covariance": "1.0 common mode; no independent RGB impulses",
        "density_scale": 0.06,
        "site_count": 900.0,
        "radius_px_at_5760": 0.30,
        "optical_sigma_px_at_5760": 0.23,
        "boundary": "subordinate prediction; 2383 covariance/NPS unpublished",
    },
    "frozen": (
        "V42 RAW interpretation, V41 12.5% chart residual, H-D curves, net "
        "dye/mask spectra, D-min, DIR coefficients, processed-stock MTF, "
        "black, contrast, gamma, exposure and delivery authority"
    ),
    "explicitly_withheld": (
        "no white-balance, saturation or aesthetic grade; no conversion of "
        "Kodak patent diffusion factor into a fictitious 5279 DIR constant"
    ),
}


def apply(module) -> None:
    v42_profile.apply(module)
    module.NEGATIVE_GRAIN_CORRELATION_SCALE = 0.72
    module.GRAIN_SIZE_CLASS_RADIUS_FACTORS = np.asarray(
        PROFILE["negative_nps_hypothesis"]["radius_factors"], dtype=np.float32
    )
    module.GRAIN_SIZE_CLASS_OPTICAL_FACTORS = np.asarray(
        PROFILE["negative_nps_hypothesis"]["optical_factors"], dtype=np.float32
    )
    fractions = np.asarray(
        PROFILE["negative_nps_hypothesis"]["population_fractions"],
        dtype=np.float32,
    )
    if fractions.shape != (3, 5) or not np.allclose(
        fractions.sum(axis=1), 1.0, atol=1e-6
    ):
        raise ValueError("V43H grain population fractions must be normalized 3x5")
    module.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION = fractions
    module.SPIRIT_PERIOD_OBSERVER_CENTRES_NM = (
        SPIRIT_PERIOD_OBSERVER_CENTRES_NM.copy()
    )
    module.SPIRIT_PERIOD_OBSERVER_SIGMAS_NM = (
        SPIRIT_PERIOD_OBSERVER_SIGMAS_NM.copy()
    )
    # The spectral LUT and the neutral-scale calibration are observer-dependent.
    module._NEGATIVE_5279_NET_DENSITY_LUT = None
    module._SPIRIT_NEUTRAL_SCALE_TABLE = None
    module.PRINT_GRAIN_DOMAIN = "hypothesis_common_density"
    module.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE = 0.06
    module.PRINT_2383_HYPOTHESIS_SITE_COUNT = 900.0
    module.PRINT_2383_HYPOTHESIS_RADIUS_PX_5760 = 0.30
    module.PRINT_2383_HYPOTHESIS_OPTICAL_SIGMA_PX_5760 = 0.23
