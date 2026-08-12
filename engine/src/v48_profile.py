"""V48 isotropic continuous-site integration candidate.

V37 stopped a frame-varying numerical phase from becoming a second animated
signal, but retained one fixed bilinear translation for each size-class field.
At native 5760-pixel width those translations create record-dependent x/y
correlation and angular NPS bias. They are a raster artifact, not a measured
property of 5279.

V48 removes the global translations. Their integration role is replaced by an
isotropic second-moment approximation to two independent uniform operations:
continuous site position inside a pixel and output pixel-area integration.
Each contributes variance 1/12 pixel squared per axis, so the equivalent
Gaussian variance is 1/6 at the 5760-pixel reference scale. This is a numerical
integration correction, not a newly claimed Kodak cloud-size measurement.
"""

from __future__ import annotations

import numpy as np

import v45_profile


INPUT_CHROMA_RESIDUAL_D50 = v45_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v45_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
SITE_AND_PIXEL_INTEGRATION_VARIANCE_PX2_5760 = 1.0 / 6.0


PROFILE = {
    **v45_profile.PROFILE,
    "name": "V48 · Isotropic continuous-site integration candidate",
    "short_name": "V48",
    "version_id": "v48",
    "release_class": "numerical_image_formation_correction",
    "image_change_from_v45": (
        "Remove record-dependent anisotropy caused by V37's fixed whole-field "
        "bilinear subpixel translations. Replace only their integration role "
        "with an isotropic second-moment site-position plus pixel-area model."
    ),
    "grain_site_rasterization": "isotropic_continuous_site_second_moment",
    "site_and_pixel_integration_variance_px2_at_5760": (
        SITE_AND_PIXEL_INTEGRATION_VARIANCE_PX2_5760
    ),
    "evidence_boundary": (
        "The removed x/y anisotropy is a demonstrated raster artifact. The "
        "isotropic variance follows uniform site-position and pixel-integration "
        "geometry; it is not a stock-specific 5279 NPS measurement."
    ),
    "frozen_from_v45": (
        "RAW colour, H-D curves, finite-site law, five size-class weights and "
        "radii, DIR, density MTF, 48-micrometre RMS authority, scan observer, "
        "2383 observer, official CIE table and delivery encodings"
    ),
}


def apply(module) -> None:
    v45_profile.apply(module)
    module.GRAIN_SUBPIXEL_PHASE_RADIUS_PX = 0.0
    module.GRAIN_SITE_RASTERIZATION_MODE = (
        "isotropic_continuous_site_second_moment"
    )
    module.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB = np.sqrt(
        np.square(module.SUBEMULSION_OPTICAL_SIGMA_BASE_PX_5760_RGB)
        + SITE_AND_PIXEL_INTEGRATION_VARIANCE_PX2_5760
    ).astype(np.float32)
