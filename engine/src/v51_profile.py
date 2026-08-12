"""V51 vector-traced 5279 net-dye and minimum-density spectra.

V50 exposed that several stock-authority arrays still came from coarse visual
transcription.  V51 samples the actual vector paths embedded in Kodak's March
2003 H-1-5279t PDF at the engine's existing 20 nm wavelength grid.  It changes
only the three D-min-subtracted, peak-normalized net separation curves and the
dashed minimum-density/orange-mask curve.  H-D, grain, DIR, 2383 and the two
observer policies remain frozen.
"""

from __future__ import annotations

import numpy as np

import v50_profile


INPUT_CHROMA_RESIDUAL_D50 = v50_profile.INPUT_CHROMA_RESIDUAL_D50
INPUT_CHROMA_RESIDUAL_STRENGTH = v50_profile.INPUT_CHROMA_RESIDUAL_STRENGTH
GRANULARITY_LOG_EXPOSURE = v50_profile.GRANULARITY_LOG_EXPOSURE
GRANULARITY_SIGMA_D_RGB = v50_profile.GRANULARITY_SIGMA_D_RGB


NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = np.array(
    [
        [0.2739296, 0.0836895, 0.2849829],
        [0.2126315, 0.0517756, 0.4649588],
        [0.1095180, 0.0242712, 0.7615403],
        [0.0374840, -0.0024237, 0.9829948],
        [0.0075843, 0.0228642, 0.9546835],
        [-0.0015856, 0.2047608, 0.6657021],
        [0.0019816, 0.5179682, 0.3767965],
        [0.0153421, 0.8284701, 0.2215723],
        [0.0618078, 1.0037871, 0.1566497],
        [0.1443314, 0.8785778, 0.1090669],
        [0.2419390, 0.5767580, 0.0615618],
        [0.4364387, 0.3795864, 0.0300416],
        [0.6310012, 0.3057750, 0.0167037],
        [0.8026121, 0.2917743, 0.0108627],
        [0.9335714, 0.2972470, 0.0081165],
        [1.0041634, 0.3002279, 0.0052692],
        [0.9783076, 0.2894932, 0.0066305],
        [0.8438800, 0.2547847, 0.0052089],
        [0.6368829, 0.2022283, 0.0052089],
        [0.4225931, 0.1431710, 0.0051052],
        [0.2479485, 0.0889471, 0.0038586],
    ],
    dtype=np.float32,
)

NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = np.array(
    [
        0.8507759, 0.7583310, 0.8091010, 0.9223479, 0.8884793,
        0.8299631, 0.7581589, 0.7016539, 0.5477439, 0.5289311,
        0.5063680, 0.2674901, 0.1787179, 0.1594032, 0.1507880,
        0.1423273, 0.1339343, 0.1254797, 0.1141805, 0.1014605,
        0.0899573,
    ],
    dtype=np.float32,
)


PROFILE = {
    **v50_profile.PROFILE,
    "name": "V51 · Vector-traced 5279 negative spectra",
    "short_name": "V51",
    "version_id": "v51",
    "release_class": "published_negative_spectral_vector_trace_correction",
    "image_change_from_v50": (
        "Replace coarse visual transcriptions of the 5279 net CMY separation "
        "curves and dashed D-min/orange-mask spectrum with values recovered "
        "from the March 2003 PDF's embedded vector paths at 20 nm intervals."
    ),
    "spectral_authority": (
        "Kodak H-1-5279t, March 2003, Spectral Dye Density Curves; ECN-2; "
        "D-mins subtracted for cyan/magenta/yellow, dashed Minimum Density "
        "retained separately"
    ),
    "evidence_boundary": (
        "V51 corrects graph transcription only. The net curves remain "
        "peak-normalized representative data, not absolute analytical dye "
        "spectra, and the proprietary Spirit optical-film-match matrix remains "
        "unmeasured."
    ),
}


def apply(module) -> None:
    v50_profile.apply(module)
    module.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY = (
        NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY.copy()
    )
    module.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY = (
        NEGATIVE_5279_DMIN_SPECTRAL_DENSITY.copy()
    )
    module.refresh_5279_spectral_observer_caches()
