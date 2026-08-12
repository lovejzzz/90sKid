"""V52 evidence-separated 5279 characteristic-curve profile.

Kodak's March 2003 PDF contains recoverable vector paths for all three Status-M
H-D curves, but the paths do not disclose a complete high-exposure shoulder.
V52 therefore keeps three evidence classes separate: a constant D-min hold
before the drawn path, vector-path samples through graph logE zero, and an
explicitly inferred continuation that preserves only the Archive shoulder
increments relative to the newly traced endpoint.
"""

from __future__ import annotations

import numpy as np

import v51_profile


INPUT_CHROMA_RESIDUAL_D50 = v51_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v51_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v51_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v51_profile.GRANULARITY_SIGMA_D_RGB
NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
    v51_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY
)
NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
    v51_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY
)


SENSITO_LOG_EXPOSURE = np.array(
    [
        -4.0,
        -3.795937,
        -3.75,
        -3.50,
        -3.25,
        -3.00,
        -2.75,
        -2.50,
        -2.25,
        -2.00,
        -1.75,
        -1.50,
        -1.25,
        -1.00,
        -0.75,
        -0.50,
        -0.25,
        0.00,
        0.50,
        1.00,
    ],
    dtype=np.float32,
)

SENSITO_DENSITY_RGB = np.array(
    [
        [
            0.1589664,
            0.1589664,
            0.1599553,
            0.1653767,
            0.1791778,
            0.2034883,
            0.2798613,
            0.4045004,
            0.5369801,
            0.6696922,
            0.8031971,
            0.9391702,
            1.0708890,
            1.1960587,
            1.3128646,
            1.4198447,
            1.5066094,
            1.5841743,
            1.7241743,
            1.8041743,
        ],
        [
            0.5950253,
            0.5950253,
            0.5955216,
            0.5992579,
            0.6097326,
            0.6395163,
            0.7264678,
            0.8682558,
            1.0200540,
            1.1722014,
            1.3236481,
            1.4772975,
            1.6294172,
            1.7719997,
            1.9051163,
            2.0261705,
            2.1225665,
            2.2142119,
            2.3742119,
            2.4642119,
        ],
        [
            0.9253015,
            0.9253015,
            0.9257941,
            0.9295179,
            0.9400236,
            0.9697940,
            1.0567439,
            1.2006632,
            1.3515267,
            1.5046250,
            1.6543876,
            1.8107150,
            1.9630531,
            2.1065841,
            2.2396944,
            2.3607723,
            2.4605023,
            2.5488544,
            2.6688544,
            2.7288544,
        ],
    ],
    dtype=np.float32,
)


PROFILE = {
    **v51_profile.PROFILE,
    "name": "V52 · Evidence-separated 5279 characteristic curves",
    "short_name": "V52",
    "version_id": "v52",
    "release_class": "published_characteristic_vector_trace_correction",
    "image_change_from_v51": (
        "Replace the coarse H-D transcription inside Kodak's plotted domain "
        "with samples from the embedded vector paths; retain the unplotted "
        "shoulder only as an explicitly identified Archive-relative inference."
    ),
    "characteristic_authority": (
        "Kodak H-1-5279t, March 2003, F010_0238AC; 3200 K, 1/50 second, "
        "ECN-2, Status M"
    ),
    "vector_axis_fit_rms_density": 0.0019466,
    "drawn_path_domain_loge": (-3.795937, 0.0),
    "outside_path_low_policy": "constant first drawn D-min value",
    "outside_graph_high_policy": (
        "new vector endpoint plus the Archive +0.5/+1.0 density increments; "
        "inferred, not published"
    ),
    "evidence_boundary": (
        "The curves are representative production-coating data, not a batch "
        "specification. V52 does not claim that the retained high-exposure "
        "shoulder, proprietary subemulsion decomposition, DIR matrix or 2383 "
        "raster transcription was measured by this graph."
    ),
}


def apply(module) -> None:
    v51_profile.apply(module)
    module.SENSITO_LOG_EXPOSURE = SENSITO_LOG_EXPOSURE.copy()
    module.SENSITO_DENSITY_RGB = SENSITO_DENSITY_RGB.copy()
    module.SENSITO_DMIN_RGB = module.SENSITO_DENSITY_RGB[:, 0].copy()
    module.NEGATIVE_5279_BASE_DENSITY_RGB = module.SENSITO_DMIN_RGB.copy()
    # Neutral scanner references and every observer product derived from formed
    # negative density must be invalidated after the H-D/D-min replacement.
    module.refresh_5279_spectral_observer_caches()
