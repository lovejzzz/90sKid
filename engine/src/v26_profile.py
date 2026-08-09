"""V26 exposure-conditioned 5279 grain morphology profile.

V25 remains the colour/output baseline.  V26 changes only how each of the
fast, medium and slow sub-emulsions distributes its already calibrated finite
site population among five dye-cloud size classes.
"""

from __future__ import annotations

import numpy as np

import v25_profile


PROFILE = {
    **v25_profile.PROFILE,
    "name": "V26 exposure-conditioned 35 mm dye-cloud spectrum",
    # Rows: fast, medium, slow.  Kodak states that the fastest grains are the
    # largest and predominate in shadows/underexposure.  5279 does not disclose
    # its exact coating distribution, so this is a bounded morphology model,
    # not a claimed formulation.  Each row sums to one.
    "grain_size_class_fractions_by_population": [
        [0.12, 0.26, 0.34, 0.20, 0.08],
        [0.16, 0.30, 0.32, 0.17, 0.05],
        [0.22, 0.34, 0.29, 0.12, 0.03],
    ],
    "mean_colour_constraint": "V25 deterministic negative and observers unchanged",
    "amplitude_constraint": "Kodak 5279 per-record diffuse RMS at 48 micrometre aperture",
}


def apply(module) -> None:
    v25_profile.apply(module)
    fractions = np.asarray(
        PROFILE["grain_size_class_fractions_by_population"], dtype=np.float32
    )
    if fractions.shape != (3, 5) or not np.allclose(
        fractions.sum(axis=1), 1.0, atol=1e-6
    ):
        raise ValueError("V26 population grain fractions must be 3x5 and sum to one")
    module.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION = fractions
