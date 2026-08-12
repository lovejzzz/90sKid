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
    module.SENSITO_LOG_EXPOSURE = module.SENSITO_LOG_EXPOSURE_ARCHIVE.copy()
    module.SENSITO_DENSITY_RGB = module.SENSITO_DENSITY_RGB_ARCHIVE.copy()
    module.SENSITO_DMIN_RGB = module.SENSITO_DENSITY_RGB[:, 0].copy()
    module.NEGATIVE_5279_BASE_DENSITY_RGB = module.SENSITO_DMIN_RGB.copy()
    module.GRANULARITY_LOG_EXPOSURE = (
        module.GRANULARITY_LOG_EXPOSURE_ARCHIVE.copy()
    )
    module.GRANULARITY_SIGMA_D_RGB = (
        module.GRANULARITY_SIGMA_D_RGB_ARCHIVE.copy()
    )
    module.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
        module.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY_ARCHIVE.copy()
    )
    module.SUBEMULSION_DYE_RECORD_MIX = (
        module.SUBEMULSION_DYE_RECORD_MIX_ARCHIVE.copy()
    )
    module.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
        module.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY_ARCHIVE.copy()
    )
    module.PRINT_2383_LOG_EXPOSURE = (
        module.PRINT_2383_LOG_EXPOSURE_ARCHIVE.copy()
    )
    module.PRINT_2383_DENSITY_RGB = (
        module.PRINT_2383_DENSITY_RGB_ARCHIVE.copy()
    )
    module.PRINT_2383_STATUS_A_DMIN_RGB = (
        module.PRINT_2383_STATUS_A_DMIN_RGB_ARCHIVE.copy()
    )
    module.PRINT_2383_DMAX = module.PRINT_2383_DMAX_ARCHIVE
    module.PRINT_2383_LOG_SENSITIVITY_CMY = (
        module.PRINT_2383_LOG_SENSITIVITY_CMY_ARCHIVE.copy()
    )
    module.PRINT_DYE_CMY_SPECTRAL_DENSITY = (
        module.PRINT_DYE_CMY_SPECTRAL_DENSITY_ARCHIVE.copy()
    )
    # V59+ can replace the clear-print spectral base. Historical profiles must
    # explicitly restore it before rebuilding scanner/monitor caches; otherwise
    # applying a later profile and then returning to V37--V45 changes pixels.
    module.PRINT_2383_DMIN_SPECTRAL_DENSITY = (
        module.PRINT_2383_DMIN_SPECTRAL_DENSITY_ARCHIVE.copy()
    )
    module.PRINT_2383_DMIN_SPECTRAL_POLICY = (
        module.PRINT_2383_DMIN_SPECTRAL_POLICY_ARCHIVE
    )
    for diagnostic in (
        "PRINT_2383_LAD_ANALYTICAL_AMOUNT_CMY",
        "PRINT_2383_LAD_INTEGRAL_RESIDUAL_RGB",
    ):
        if hasattr(module, diagnostic):
            delattr(module, diagnostic)
    module.KODAK_XENON_PROJECTOR_RELATIVE_SPD = (
        module.KODAK_XENON_PROJECTOR_RELATIVE_SPD_ARCHIVE.copy()
    )
    module.PRINT_MONITOR_COLOUR_AUTHORITY = (
        module.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE
    )
    module.PRINT_2383_INTERIMAGE_MATRIX = (
        module.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE.copy()
    )
    module.PRINT_2383_INTERIMAGE_POLICY = (
        module.PRINT_2383_INTERIMAGE_POLICY_ARCHIVE
    )
    module.PRINT_2383_VIEW_NEUTRAL_POLICY = (
        module.PRINT_2383_VIEW_NEUTRAL_POLICY_ARCHIVE
    )
    module.PRINT_2383_DENSITY_NEUTRAL_POLICY = (
        module.PRINT_2383_DENSITY_NEUTRAL_POLICY_ARCHIVE
    )
    module.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB = (
        module.PRINT_2383_LAD_STATUS_A_AIM_RGB.copy()
    )
    module.PRINT_2383_LAD_PRINCIPAL_POLICY = (
        module.PRINT_2383_LAD_PRINCIPAL_POLICY_ARCHIVE
    )
    module.SPIRIT_PRIMARY_CORRECTION_TARGET = (
        module.SPIRIT_PRIMARY_CORRECTION_TARGET_ARCHIVE
    )
    module.NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY = (
        module.NEGATIVE_5279_PRINTER_DENSITY_OBSERVER_POLICY_ARCHIVE
    )
    module.refresh_5279_spectral_observer_caches()
    module.GRAIN_SUBPIXEL_PHASE_MODE = "stable_balanced"
    module.GRAIN_SUBPIXEL_PHASE_RADIUS_PX = PROFILE[
        "grain_subpixel_phase_radius_native_px"
    ]
    module.GRAIN_STABLE_PHASE_OFFSET_RADIANS = math.pi / 6.0
    module.GRAIN_SITE_RASTERIZATION_MODE = "fixed_global_bilinear_phase"
    module.GRAIN_LOCAL_DENSITY_BOUND_MODE = "legacy_macro_dmax_plus_0_12"
    module.GRAIN_STOCHASTIC_EXPOSURE_POLICY = (
        "legacy_target_only_endpoint_hold"
    )
    module.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB = (
        module.SUBEMULSION_OPTICAL_SIGMA_BASE_PX_5760_RGB.copy()
    )
