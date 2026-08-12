"""V61 ISO Status-M and joint 5279 analytical-density correction.

V51 recovered Kodak's peak-normalized net dye spectra, but V42--V60 still
converted the published Status-M H-D readings with three independent Gaussian
bands. That is not a valid coordinate for a masked colour negative: every
receiver integrates D-min plus all three net dye/coupler spectra. V61 restores
ISO 5-3 Status-M spectral products and jointly inverts the three integral
readings to nonnegative analytical CMY amounts before either scanning or
optical printing.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

import v60_profile


INPUT_CHROMA_RESIDUAL_D50 = v60_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v60_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v60_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v60_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v60_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v60_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v60_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v60_profile.SENSITO_DENSITY_RGB
PRINT_2383_LOG_EXPOSURE = v60_profile.PRINT_2383_LOG_EXPOSURE
PRINT_2383_DENSITY_RGB = v60_profile.PRINT_2383_DENSITY_RGB
PRINT_2383_STATUS_A_DMIN_RGB = v60_profile.PRINT_2383_STATUS_A_DMIN_RGB
PRINT_2383_DMAX = v60_profile.PRINT_2383_DMAX
PRINT_2383_LOG_SENSITIVITY_CMY = v60_profile.PRINT_2383_LOG_SENSITIVITY_CMY
PRINT_DYE_CMY_SPECTRAL_DENSITY = v60_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY
PRINT_2383_DMIN_SPECTRAL_DENSITY = (
    v60_profile.PRINT_2383_DMIN_SPECTRAL_DENSITY
)
PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY = (
    v60_profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY
)
TRACE_SHA256 = v60_profile.TRACE_SHA256


STATUS_M_TABLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data/iso5_3_1984_status_m_log_spectral_products.csv"
)
STATUS_M_TABLE_SHA256 = (
    "732313ea2103ded0673bf99dfe8b2c6b964afede553fcb8a112af6497f5176f3"
)
STATUS_M_WAVELENGTHS_NM = np.arange(380.0, 781.0, 1.0, dtype=np.float32)
_TAIL_SLOPES_LOG10_PER_NM = {
    "red": (0.260, -0.040),
    "green": (0.106, -0.120),
    "blue": (0.250, -0.220),
}


def _load_iso_status_m_weights() -> np.ndarray:
    digest = hashlib.sha256(STATUS_M_TABLE_PATH.read_bytes()).hexdigest()
    if digest != STATUS_M_TABLE_SHA256:
        raise ValueError(
            "ISO Status-M table checksum mismatch: "
            f"expected {STATUS_M_TABLE_SHA256}, got {digest}"
        )
    with STATUS_M_TABLE_PATH.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))

    log_products = []
    for channel in ("red", "green", "blue"):
        selected = [row for row in rows if row["channel"] == channel]
        axis = np.asarray(
            [float(row["wavelength_nm"]) for row in selected],
            dtype=np.float64,
        )
        values = np.asarray(
            [float(row["log10_spectral_product"]) for row in selected],
            dtype=np.float64,
        )
        if not np.all(np.diff(axis) == 10.0) or np.max(values) != 5.0:
            raise ValueError(f"unexpected ISO Status-M {channel} table")
        interpolated = np.interp(STATUS_M_WAVELENGTHS_NM, axis, values)
        lower_slope, upper_slope = _TAIL_SLOPES_LOG10_PER_NM[channel]
        lower = STATUS_M_WAVELENGTHS_NM < axis[0]
        upper = STATUS_M_WAVELENGTHS_NM > axis[-1]
        interpolated[lower] = values[0] + lower_slope * (
            STATUS_M_WAVELENGTHS_NM[lower] - axis[0]
        )
        interpolated[upper] = values[-1] + upper_slope * (
            STATUS_M_WAVELENGTHS_NM[upper] - axis[-1]
        )
        log_products.append(interpolated)

    weights = np.power(10.0, np.column_stack(log_products) - 5.0)
    weights /= np.sum(weights, axis=0, keepdims=True)
    return weights.astype(np.float32)


STATUS_M_RGB_WEIGHTS = _load_iso_status_m_weights()


PROFILE = {
    **v60_profile.PROFILE,
    "name": "V61 · ISO Status-M joint negative analytical density",
    "short_name": "V61",
    "version_id": "v61",
    "release_class": "evidence_corrected_5279_status_m_joint_inverse",
    "image_change_from_v60": (
        "Replace the independent 690/550/450 nm Gaussian negative-density "
        "axes with ISO 5-3 Status-M spectral products and jointly solve all "
        "three integral readings through the complete 5279 D-min plus net "
        "dye/masking-coupler spectra."
    ),
    "negative_status_m_table_sha256": STATUS_M_TABLE_SHA256,
    "negative_status_m_policy": "iso5_3_spectral_products_1nm_v61",
    "negative_analytical_density_policy": "joint_iso_status_m_v61",
    "evidence_boundary": (
        "ISO 5-3 defines the receiver, and Kodak H-1-5279t supplies only "
        "representative 20 nm graph traces. V61 linearly interpolates those "
        "density curves to the 1 nm receiver grid. Unreachable independent "
        "Status-M triplets are projected to the nearest nonnegative dye "
        "mixture; the proprietary 5279 interimage transform remains unknown."
    ),
}


def apply(module) -> None:
    v60_profile.apply(module)
    module.NEGATIVE_5279_STATUS_M_WAVELENGTHS_NM = (
        STATUS_M_WAVELENGTHS_NM.copy()
    )
    module.NEGATIVE_5279_STATUS_M_RGB_WEIGHTS = STATUS_M_RGB_WEIGHTS.copy()
    module.NEGATIVE_5279_STATUS_M_POLICY = "iso5_3_spectral_products_1nm_v61"
    module.NEGATIVE_5279_ANALYTICAL_DENSITY_POLICY = "joint_iso_status_m_v61"
    module.refresh_5279_spectral_observer_caches()
