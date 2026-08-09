#!/usr/bin/env python3
"""Non-release probe: integrate V31 while freezing the complete V30 image model."""

from __future__ import annotations

import sys
from pathlib import Path

import render_v28_dual_masters
import v30_profile


PROFILE = {
    **v30_profile.PROFILE,
    "version_id": "v34-pipeline-probe",
    "short_name": "V34 pipeline probe",
    "name": "V34 pipeline-only single-generation probe",
    "final_projection_adapter": "v31_scan_low_frequency_chroma",
    "projection_chroma_crossover_sigma_at_2k": 0.72,
    "projection_change": (
        "accepted V31 adapter moved before the only ProRes generation; all "
        "V30 image-model operations and floating-point matrix order frozen"
    ),
}


def apply(module) -> None:
    v30_profile.apply(module)


def main() -> None:
    render_v28_dual_masters.v28_profile = sys.modules[__name__]
    render_v28_dual_masters.DEFAULT_PRINT_LUT_CACHE = (
        Path(__file__).resolve().parents[1]
        / "cache"
        / "print_2383_monitor_output_lut_193_v30.npy"
    )
    render_v28_dual_masters.EXPECTED_PRINT_LUT_SHA256 = (
        "5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c"
    )
    render_v28_dual_masters.main()


if __name__ == "__main__":
    main()
