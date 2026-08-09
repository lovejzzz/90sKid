"""V25 corrected delivery output and deterministic parallel-emulsion profile."""

from __future__ import annotations

import os

import v24_profile


PROFILE = {
    **v24_profile.PROFILE,
    "name": "V25 corrected reference-delivery pipeline",
    "binomial_sampler": "fixed seeded stripes; exact binomial distribution",
    "binomial_random_stripes": 8,
    "binomial_parallel_workers": 8,
    "projection_output": "Rec.709-D65 monitor rendering of the 48-nit gamma-2.6 cinema observer; Rec.709 OETF / 1-1-1",
    "bluray_output": "Rec.709-D65 OETF / 1-1-1; BT.1886 retained as reference-display EOTF",
    "web_output": "sRGB IEC 61966-2-1 derived from decoded Rec.709 master light",
}


def apply(module) -> None:
    # V24 is the accepted baseline. V25 changes no sensitometry, dye spectra,
    # MTF, grain scale, DIR chemistry, scanner observer or finishing curve.
    v24_profile.apply(module)
    # Re-applying V25 after a newer profile must restore the shared V24/V25
    # distribution rather than retaining process-global V26 state.
    module.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION = None
    # Re-applying an older profile after V27 must also restore the former
    # two-anchor scanner observer exactly.
    if hasattr(module, "SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED"):
        module.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED = False
        module._SPIRIT_NEUTRAL_SCALE_TABLE = None
    module.BINOMIAL_SAMPLER_MODE = "striped_v25"
    module.BINOMIAL_RANDOM_STRIPES = PROFILE["binomial_random_stripes"]
    module.BINOMIAL_PARALLEL_WORKERS = int(
        os.environ.get(
            "V25_BINOMIAL_WORKERS", PROFILE["binomial_parallel_workers"]
        )
    )
