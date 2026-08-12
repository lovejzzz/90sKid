"""V53 vector-traced 2383 characteristic-curve correction.

V53 inherits V52 in full and changes only the release-print Status-A H-D
curves.  The table is recovered from the original vector nodes embedded in
Kodak H-1-2383t (March 2005), an era-appropriate sheet for 5279.  Spectral
sensitivity, dye density, projector SPD, negative formation, DIR, MTF and grain
remain frozen so the sensitometric correction can be judged in isolation.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import numpy as np

import v52_profile


INPUT_CHROMA_RESIDUAL_D50 = v52_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v52_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v52_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v52_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v52_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v52_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)
SENSITO_LOG_EXPOSURE = v52_profile.SENSITO_LOG_EXPOSURE
SENSITO_DENSITY_RGB = v52_profile.SENSITO_DENSITY_RGB


TRACE_PATH = Path(__file__).resolve().parents[1] / "data/2383_characteristic_trace_2005.csv"
TRACE_SHA256 = "e7d7eba838222828df9e538f19805725369a163ed57ca037dd212fd6878430cd"


def _load_trace() -> tuple[np.ndarray, np.ndarray]:
    digest = hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest()
    if digest != TRACE_SHA256:
        raise ValueError(
            f"2383 characteristic trace integrity mismatch: expected "
            f"{TRACE_SHA256}, got {digest}"
        )
    with TRACE_PATH.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    log_exposure = np.array(
        [float(row["log_exposure"]) for row in rows], dtype=np.float32
    )
    density_rgb = np.array(
        [
            [
                float(row["red_status_a_density"]),
                float(row["green_status_a_density"]),
                float(row["blue_status_a_density"]),
            ]
            for row in rows
        ],
        dtype=np.float32,
    ).T
    return log_exposure, density_rgb


PRINT_2383_LOG_EXPOSURE, PRINT_2383_DENSITY_RGB = _load_trace()
PRINT_2383_STATUS_A_DMIN_RGB = PRINT_2383_DENSITY_RGB[:, 0].copy()
PRINT_2383_DMAX = float(np.max(PRINT_2383_DENSITY_RGB))


PROFILE = {
    **v52_profile.PROFILE,
    "name": "V53 · Vector-traced 2383 characteristic curves",
    "short_name": "V53",
    "version_id": "v53",
    "release_class": "published_2383_characteristic_vector_trace_correction",
    "image_change_from_v52": (
        "Replace the coarse 2026 2383 visual transcription with the union of "
        "all vector nodes in Kodak's March 2005 Status-A sensitometric graph; "
        "make the per-record D-min values internally consistent."
    ),
    "print_characteristic_authority": (
        "Kodak H-1-2383t, March 2005, F002_1254AC; 1/500 second, tungsten "
        "with Heat Absorbing Glass No. 2043 and Series 1700 filter, ECP-2D, "
        "Status A"
    ),
    "print_characteristic_trace_sha256": TRACE_SHA256,
    "print_vector_axis_fit_rms_density": 0.0009894,
    "print_outside_path_policy": (
        "constant first/last vector density to the graph borders at logE "
        "-3/+3; explicitly classified as endpoint holds, not measured path"
    ),
    "evidence_boundary": (
        "V53 isolates the 2383 H-D correction. It does not yet replace the "
        "runtime 2383 spectral-sensitivity or dye-density transcriptions, "
        "infer proprietary interimage chemistry, or add a creative grade."
    ),
}


def apply(module) -> None:
    v52_profile.apply(module)
    module.PRINT_2383_LOG_EXPOSURE = PRINT_2383_LOG_EXPOSURE.copy()
    module.PRINT_2383_DENSITY_RGB = PRINT_2383_DENSITY_RGB.copy()
    module.PRINT_2383_STATUS_A_DMIN_RGB = (
        PRINT_2383_STATUS_A_DMIN_RGB.copy()
    )
    module.PRINT_2383_DMAX = PRINT_2383_DMAX
    # The neutral-scale shapers, print exposure aim and output observer lattice
    # all depend on the positive-stock H-D curves.
    module.refresh_5279_spectral_observer_caches()
