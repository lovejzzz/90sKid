"""V59 vector-traced 2383 D-min/base spectral-density correction.

V55 traced the cyan, magenta and yellow curves from Kodak F010_0294AC but
omitted the fourth plotted curve, ``Visual Neutral``. The three dye curves are
peak-normalized; their sum does not contain the processed print's minimum/base
spectral density. V59 derives that missing nonnegative spectrum as the official
visual-neutral curve minus the sum of the three normalized dyes, then uses it
in Status-A inversion and projected transmission. All negative-film,
interimage and scan-referenced observer choices remain those of V58.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

import v58_profile


INPUT_CHROMA_RESIDUAL_D50 = v58_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v58_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v58_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v58_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v58_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v58_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v58_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v58_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v58_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v58_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v58_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v58_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v58_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v58_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY


TRACE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data/2383_visual_neutral_trace_2005.csv"
)
TRACE_SHA256 = "9bc1645f4afe79e01e917dc11c556d671eb2c3b367b884807e010d509bd1e90e"


def _load_visual_neutral() -> np.ndarray:
    digest = hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest()
    if digest != TRACE_SHA256:
        raise ValueError(
            f"2383 visual-neutral trace mismatch: expected {TRACE_SHA256}, got {digest}"
        )
    with TRACE_PATH.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    wavelengths = np.asarray(
        [float(row["wavelength_nm"]) for row in rows], dtype=np.float32
    )
    expected = np.arange(380.0, 781.0, 20.0, dtype=np.float32)
    if not np.array_equal(wavelengths, expected):
        raise ValueError("2383 visual-neutral trace has an unexpected axis")
    return np.asarray(
        [float(row["visual_neutral_density"]) for row in rows],
        dtype=np.float32,
    )


PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY = _load_visual_neutral()
PRINT_2383_DMIN_SPECTRAL_DENSITY = np.maximum(
    PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY
    - np.sum(PRINT_DYE_CMY_SPECTRAL_DENSITY, axis=1),
    0.0,
).astype(np.float32)


PROFILE = {
    **v58_profile.PROFILE,
    "name": "V59 · Vector-traced 2383 base spectrum",
    "short_name": "V59",
    "version_id": "v59",
    "release_class": "published_2383_visual_neutral_vector_trace_correction",
    "image_change_from_v58": (
        "Restore the processed 2383 base/D-min spectral density omitted in "
        "V55 by subtracting the normalized C/M/Y dye sum from Kodak's fourth "
        "Visual Neutral curve."
    ),
    "print_visual_neutral_trace_sha256": TRACE_SHA256,
    "print_dmin_spectral_policy": "vector_neutral_residual_v59",
    "lad_coordinate_policy": "integral_spectral_inverse_v59",
    "evidence_boundary": (
        "The 380..740 nm neutral and dye samples are vector paths from Kodak "
        "H-1-2383t F010_0294AC. 760/780 nm are disclosed terminal-secant "
        "continuations. The residual is clipped only at zero. The generic "
        "xenon lamp graph, empirical interimage and scan-referenced monitor "
        "observer remain unchanged."
    ),
}


def apply(module) -> None:
    v58_profile.apply(module)
    module.PRINT_2383_DMIN_SPECTRAL_DENSITY = (
        PRINT_2383_DMIN_SPECTRAL_DENSITY.copy()
    )
    module.PRINT_2383_DMIN_SPECTRAL_POLICY = "vector_neutral_residual_v59"
    principal, amounts, residual = module.solve_2383_lad_principal_density_rgb(
        module.PRINT_2383_LAD_STATUS_A_AIM_RGB
    )
    module.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB = principal
    module.PRINT_2383_LAD_ANALYTICAL_AMOUNT_CMY = amounts
    module.PRINT_2383_LAD_INTEGRAL_RESIDUAL_RGB = residual
    module.PRINT_2383_LAD_PRINCIPAL_POLICY = "integral_spectral_inverse_v59"
    module.refresh_5279_spectral_observer_caches()
