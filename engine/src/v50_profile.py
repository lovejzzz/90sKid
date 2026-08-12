"""V50 evidence-traced 5279 diffuse-RMS granularity profile.

The Archive table was a coarse visual transcription and included an invented
sample one log-exposure unit beyond Kodak's plotted range.  V50 samples the
actual Bezier paths embedded in Kodak's March 2003 H-1-5279t PDF at half-logE
intervals and calibrates their y coordinates against the graph's printed
logarithmic Sigma-D ticks.  It changes only the public 48-micrometre marginal
RMS target; V49 morphology, colour and observer stages remain frozen.
"""

from __future__ import annotations

import numpy as np

import v49_profile


INPUT_CHROMA_RESIDUAL_D50 = v49_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v49_profile.INPUT_CHROMA_RESIDUAL_STRENGTH


GRANULARITY_LOG_EXPOSURE = np.array(
    [-4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0],
    dtype=np.float32,
)
GRANULARITY_SIGMA_D_RGB = np.array(
    [
        [
            0.0054329,
            0.0064795,
            0.0136699,
            0.0106630,
            0.0072010,
            0.0070468,
            0.0068959,
            0.0067482,
            0.0066036,
        ],
        [
            0.0129243,
            0.0143390,
            0.0190857,
            0.0154977,
            0.0116326,
            0.0094602,
            0.0083289,
            0.0074934,
            0.0067883,
        ],
        [
            0.0228430,
            0.0258930,
            0.0390398,
            0.0445431,
            0.0313124,
            0.0227724,
            0.0187934,
            0.0158064,
            0.0142716,
        ],
    ],
    dtype=np.float32,
)


PROFILE = {
    **v49_profile.PROFILE,
    "name": "V50 · Evidence-traced 5279 diffuse-RMS curve",
    "short_name": "V50",
    "version_id": "v50",
    "release_class": "published_granularity_vector_trace_correction",
    "image_change_from_v49": (
        "Replace the coarse hand transcription of Kodak graph F002_0269AC "
        "with samples taken from the March 2003 PDF's embedded vector paths; "
        "remove the unplotted +1 logE sample and hold the last published "
        "endpoint outside the graph domain."
    ),
    "granularity_authority": (
        "Kodak H-1-5279t, March 2003, F002_0269AC; RGB density sigma through "
        "a 48-micrometre microdensitometer aperture"
    ),
    "trace_method": (
        "embedded cubic Bezier paths sampled every 0.5 graph-logE unit; "
        "Sigma-D recovered from least-squares calibration of all twelve "
        "printed logarithmic axis ticks"
    ),
    "trace_axis_fit_rms_pdf_points": 0.4596,
    "outside_published_loge_domain": (
        "constant endpoint via numpy.interp; no invented continuation"
    ),
    "evidence_boundary": (
        "V50 corrects the published marginal RMS authority only. It does not "
        "identify 5279 NPS, cloud radii, base/fog decomposition, cross-record "
        "covariance, higher-order tails or microscopic coating capacity."
    ),
}


def apply(module) -> None:
    v49_profile.apply(module)
    module.GRANULARITY_LOG_EXPOSURE = GRANULARITY_LOG_EXPOSURE.copy()
    module.GRANULARITY_SIGMA_D_RGB = GRANULARITY_SIGMA_D_RGB.copy()
