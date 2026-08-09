#!/usr/bin/env python3
"""Render V39 through the density-formation reconstruction graph."""

from __future__ import annotations

from pathlib import Path

import render_v28_dual_masters
import v39_profile


PRINT_LUT = (
    Path(__file__).resolve().parents[1]
    / "cache"
    / "print_2383_monitor_output_lut_193_v30.npy"
)
PRINT_LUT_SHA256 = (
    "5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c"
)


def main() -> None:
    render_v28_dual_masters.v28_profile = v39_profile
    # Retained for Archive/profile validation. V39's spatially formed print
    # density uses the analytical observer instead of the pointwise output LUT.
    render_v28_dual_masters.DEFAULT_PRINT_LUT_CACHE = PRINT_LUT
    render_v28_dual_masters.EXPECTED_PRINT_LUT_SHA256 = PRINT_LUT_SHA256
    render_v28_dual_masters.main()


if __name__ == "__main__":
    main()
