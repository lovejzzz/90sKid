"""V55 vector-traced 2383 formed-dye spectral-density correction.

V55 inherits V54 and replaces only the 2383 cyan-, magenta- and yellow-forming
dye absorption spectra used by the analytical projection observer.  Samples
through 740 nm are vector-path interpolations from Kodak's March 2005 graph;
760/780 nm are disclosed terminal-secant continuations beyond its 750 nm edge.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

import v54_profile


INPUT_CHROMA_RESIDUAL_D50 = v54_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v54_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v54_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v54_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v54_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v54_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v54_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v54_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v54_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v54_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v54_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v54_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v54_profile.PRINT_2383_LOG_SENSITIVITY_CMY


TRACE_PATH = Path(__file__).resolve().parents[1] / "data/2383_dye_density_trace_2005.csv"
TRACE_SHA256 = "5f1fb8614716685c53da3191285ec33fe3d7040889159c35f5a53d274a103184"


def _load_trace() -> np.ndarray:
    digest = hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest()
    if digest != TRACE_SHA256:
        raise ValueError(
            f"2383 dye trace integrity mismatch: expected {TRACE_SHA256}, got {digest}"
        )
    with TRACE_PATH.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    wavelengths = np.array(
        [float(row["wavelength_nm"]) for row in rows], dtype=np.float32
    )
    expected = np.arange(380.0, 781.0, 20.0, dtype=np.float32)
    if not np.array_equal(wavelengths, expected):
        raise ValueError("2383 dye trace has an unexpected wavelength axis")
    return np.array(
        [
            [
                float(row["cyan_relative_density"]),
                float(row["magenta_relative_density"]),
                float(row["yellow_relative_density"]),
            ]
            for row in rows
        ],
        dtype=np.float32,
    )


PRINT_DYE_CMY_SPECTRAL_DENSITY = _load_trace()


PROFILE = {
    **v54_profile.PROFILE,
    "name": "V55 · Vector-traced 2383 dye spectra",
    "short_name": "V55",
    "version_id": "v55",
    "release_class": "published_2383_dye_vector_trace_correction",
    "image_change_from_v54": (
        "Replace the wavelength-shifted coarse 2383 formed-dye absorption "
        "table with March 2005 vector-path samples in the spectral projection "
        "observer."
    ),
    "print_dye_trace_sha256": TRACE_SHA256,
    "print_dye_authority": (
        "Kodak H-1-2383t, March 2005, F010_0294AC; process CP-2D; formed dye "
        "absorptions normalized to visual-neutral density 1.0 for xenon-arc "
        "viewing; C/M/Y curves described by Kodak as peak-normalized"
    ),
    "print_dye_outside_graph_policy": (
        "760/780 nm continue the final vector secant beyond the 750 nm graph "
        "border and clip at zero; all 380..740 nm runtime samples are within "
        "the drawn vector paths"
    ),
    "evidence_boundary": (
        "V55 corrects formed-dye spectral shape only. It retains the Archive "
        "xenon SPD, Callier gains and display adaptation; the two extrapolated "
        "far-red samples are inference rather than Kodak measurements."
    ),
}


def apply(module) -> None:
    v54_profile.apply(module)
    module.PRINT_2383_DMIN_SPECTRAL_DENSITY = (
        module.PRINT_2383_DMIN_SPECTRAL_DENSITY_ARCHIVE.copy()
    )
    module.PRINT_2383_DMIN_SPECTRAL_POLICY = (
        module.PRINT_2383_DMIN_SPECTRAL_POLICY_ARCHIVE
    )
    module.PRINT_DYE_CMY_SPECTRAL_DENSITY = (
        PRINT_DYE_CMY_SPECTRAL_DENSITY.copy()
    )
    module.refresh_5279_spectral_observer_caches()
