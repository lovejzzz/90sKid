"""V39 density-formation reconstruction profile.

V39 resolves the structural findings from the complete research/code audit.
Colour authority, characteristic curves, black, gamma and delivery encodings
remain V38.  The change is where image structure is formed and measured.
"""

from __future__ import annotations

import v38_profile


PROFILE = {
    **v38_profile.PROFILE,
    "name": "V39 · 5279 Baseline · density-formation reconstruction",
    "short_name": "V39",
    "version_id": "v39",
    "image_change_from_v38": (
        "Move 5279 MTF, 2383 MTF and 2383 finite dye-cloud structure from "
        "display residuals into their measured density domains; calibrate "
        "5279 stochastic dye yield before DIR transport; retain signed wide-"
        "gamut basis values until the three film-record exposures are formed."
    ),
    "negative_structure_domain": "processed 5279 record density",
    "negative_granularity_calibration": (
        "Kodak diffuse 48-micrometre RMS constrains source-record developed "
        "dye yield before stochastic DIR/interimage transport"
    ),
    "print_structure_domain": "formed 2383 Status-A density",
    "print_grain_model": (
        "independent finite Poisson dye-cloud realizations per 2383 record; "
        "no display-ratio overlay"
    ),
    "raw_record_boundary": (
        "preserve signed BT.2020-to-film-basis values through the record "
        "matrix and clamp physical film-record exposure once afterward"
    ),
    "frozen_observer_contract": (
        "V38 sensitometry, colour calibration authority, black, contrast, "
        "gamma, BT.1886 master and sRGB companion remain unchanged"
    ),
    "source_of_truth_fixes": (
        "profile owns stable subpixel radius explicitly; active profile owns "
        "projection adapter crossover; Archive resets are idempotent"
    ),
}


def apply(module) -> None:
    v38_profile.apply(module)
    module.FILM_RGB_CLIP_BEFORE_RECORDS = False
    module.FILM_RECORD_BOUNDARY_MODE = "signed"
    module.GRAIN_CALIBRATION_DOMAIN = "pre_dir_dye_yield"
    module.IMAGE_STRUCTURE_DOMAIN = "formed_density"
    module.PRINT_GRAIN_DOMAIN = "print_density"
    module.FORMED_DENSITY_OBSERVER_GRAIN_MANAGEMENT = False
    module.PROJECTION_GRAIN_DELTA_OBSERVER = "formed_density"
    module.GRAIN_SUBPIXEL_PHASE_RADIUS_PX = PROFILE[
        "grain_subpixel_phase_radius_native_px"
    ]
