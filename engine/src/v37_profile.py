"""V37 temporally stable 35 mm grain-formation candidate.

V37 changes only the numerical placement of the already accepted 45 finite-site
size-class fields.  Every film frame still receives independent microscopic
site activation.  The low-discrepancy subpixel phase ensemble is fixed across
time so the raster integration kernel cannot become a second animated signal.
"""

from __future__ import annotations

import math

import v36_profile


PROFILE = {
    **v36_profile.PROFILE,
    "name": "V37 · 5279 Baseline · stable emulsion sampling",
    "short_name": "V37",
    "version_id": "v37",
    "image_change_from_v36": (
        "Keep independent grain sites in every film frame, but replace the "
        "per-frame rotating 0.38-pixel numerical phase with one temporally "
        "fixed, low-discrepancy 45-class phase ensemble. Colour, H-D, diffuse "
        "48-micrometre RMS, MTF, DIR, black, gamma and observers are frozen."
    ),
    "grain_temporal_contract": (
        "independent finite-site activation per exposed film frame; stable "
        "raster integration kernel; no temporal smoothing, grain advection, "
        "fixed grain plate or per-shot aesthetic seed"
    ),
    "grain_subpixel_phase_mode": "stable_balanced",
    "grain_subpixel_phase_radius_native_px": 0.38,
    "grain_stable_phase_offset_degrees": 30.0,
    "pipeline_change": (
        "retain the validated V35 Production graph and Philox-u32 sampler; "
        "remove only frame-varying numerical subpixel phase from grain "
        "rasterization"
    ),
}


def apply(module) -> None:
    v36_profile.apply(module)
    module.GRAIN_SUBPIXEL_PHASE_MODE = "stable_balanced"
    module.GRAIN_SUBPIXEL_PHASE_RADIUS_PX = PROFILE[
        "grain_subpixel_phase_radius_native_px"
    ]
    module.GRAIN_STABLE_PHASE_OFFSET_RADIANS = math.pi / 6.0
