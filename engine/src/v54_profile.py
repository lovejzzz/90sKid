"""V54 vector-traced 2383 record-sensitivity correction.

V54 inherits V53 and replaces only the 2383 cyan-, magenta- and yellow-forming
record sensitivity spectra.  The short-wave cyan/magenta lobes and main record
bands come directly from the March 2005 PDF vector paths.  Dye spectra remain
frozen for a later isolated test.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

import v53_profile


INPUT_CHROMA_RESIDUAL_D50 = v53_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v53_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v53_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v53_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v53_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v53_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v53_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v53_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v53_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v53_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v53_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v53_profile.PRINT_2383_DMAX


TRACE_PATH = Path(__file__).resolve().parents[1] / "data/2383_log_sensitivity_trace_2005.csv"
TRACE_SHA256 = "3451b5dda9a47ff834e6a4341372fe0ecd99b6338ec8af2bdcc67fa928be720f"


def _load_trace() -> np.ndarray:
    digest = hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest()
    if digest != TRACE_SHA256:
        raise ValueError(
            f"2383 sensitivity trace integrity mismatch: expected "
            f"{TRACE_SHA256}, got {digest}"
        )
    with TRACE_PATH.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    wavelengths = np.array(
        [float(row["wavelength_nm"]) for row in rows], dtype=np.float32
    )
    expected = np.arange(380.0, 781.0, 20.0, dtype=np.float32)
    if not np.array_equal(wavelengths, expected):
        raise ValueError("2383 sensitivity trace has an unexpected wavelength axis")
    return np.array(
        [
            [
                float(row["cyan_log_sensitivity"]),
                float(row["magenta_log_sensitivity"]),
                float(row["yellow_log_sensitivity"]),
            ]
            for row in rows
        ],
        dtype=np.float32,
    )


PRINT_2383_LOG_SENSITIVITY_CMY = _load_trace()


PROFILE = {
    **v53_profile.PROFILE,
    "name": "V54 · Vector-traced 2383 record sensitivity",
    "short_name": "V54",
    "version_id": "v54",
    "release_class": "published_2383_sensitivity_vector_trace_correction",
    "image_change_from_v53": (
        "Replace the coarse 2383 C/M/Y log-sensitivity transcription with "
        "March 2005 vector-path samples, including the plotted short-wave "
        "cyan and magenta sensitivity lobes."
    ),
    "print_sensitivity_trace_sha256": TRACE_SHA256,
    "print_sensitivity_outside_path_policy": (
        "log10 sensitivity -6 outside each drawn path; this is an explicit "
        "below-graph numerical floor, not a measured response"
    ),
    "evidence_boundary": (
        "V54 changes optical printer exposure weighting only. The 2383 dye "
        "spectra and xenon SPD remain the Archive transcription so sensitivity "
        "and viewing-spectrum errors cannot compensate each other invisibly."
    ),
}


def apply(module) -> None:
    v53_profile.apply(module)
    module.PRINT_2383_LOG_SENSITIVITY_CMY = (
        PRINT_2383_LOG_SENSITIVITY_CMY.copy()
    )
    module.refresh_5279_spectral_observer_caches()
