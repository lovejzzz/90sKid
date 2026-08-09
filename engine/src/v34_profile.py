"""V34 processed-MTF and single-generation delivery profile.

V34 is an evidence correction and pipeline consolidation, not an artistic
grade.  Kodak's published 5279 MTF is for tungsten-exposed film after ECN-2
processing and already includes developer-adjacency acutance.  V21 later added
a second deterministic density-domain adjacency term without refitting that
total response.  V34 removes only that duplicate neutral-edge term; its
underidentified interimage transport and stochastic morphology remain frozen.

The accepted V31 projection colour boundary is moved before delivery encoding,
so projection and scan are formed from one in-memory negative and each receives
one ProRes generation.  The AVFoundation BT.2020 -> film-input primary transform
is algebraically fused through the otherwise idle V-Gamut round trip.
"""

from __future__ import annotations

import numpy as np

import v30_profile


PROFILE = {
    **v30_profile.PROFILE,
    "version_id": "v34",
    "short_name": "V34",
    "name": "V34 processed-MTF and single-generation baseline",
    "final_projection_adapter": "v31_scan_low_frequency_chroma",
    "projection_chroma_crossover_sigma_at_2k": 0.72,
    "projection_change": (
        "accepted V31 low-frequency scan dye colour plus projection luma and "
        "high-frequency opponent texture, applied in linear Rec.709 before "
        "the only delivery encode"
    ),
    "negative_change": (
        "remove the duplicate deterministic V21 intralayer adjacency term; "
        "retain Kodak-processed-stock MTF, interimage transport, stochastic "
        "coupling, published H-D and 48-micrometre RMS constraints"
    ),
    "pipeline_change": (
        "fuse the algebraically cancelling BT.2020->V-Gamut->Rec.709 primary "
        "round trip; integrate the V31 adapter; one ProRes generation/master"
    ),
    "raw_colour_transform": (
        "Apple extended-linear BT.2020/D65 -> fused product of the historical "
        "XYZ/V-Gamut/XYZ/Rec.709 primary matrices; no camera LUT or new white balance"
    ),
    "negative_constraint": (
        "5279 published H-D, dye spectra, exposure-conditioned 48-micrometre "
        "RMS, stochastic morphology and cross-record interimage are frozen; "
        "the published processed-stock MTF owns deterministic adjacency once"
    ),
    "film_constraint": (
        "V30/V29 5279 sensitometry, grain amplitude and morphology, stochastic "
        "DIR/interimage, RAW input, scan observer, black, gamma and Rec.709 "
        "delivery remain unchanged; deterministic neutral-edge acutance is "
        "owned once by Kodak's published processed-film MTF"
    ),
}


def apply(module) -> None:
    v30_profile.apply(module)
    module.AVFOUNDATION_DIRECT_FILM_MATRIX_ENABLED = True
    module.DIR_DETERMINISTIC_INTRALAYER_STRENGTH_RGB = np.zeros(
        3, dtype=np.float32
    )
