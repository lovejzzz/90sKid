#!/usr/bin/env python3
"""Render V35 through the validated Production execution graph."""

from __future__ import annotations

from pathlib import Path

import render_v28_dual_masters
import v35_profile


PRINT_LUT = (
    Path(__file__).resolve().parents[1]
    / "cache"
    / "print_2383_monitor_output_lut_193_v30.npy"
)
PRINT_LUT_SHA256 = (
    "5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c"
)


def main() -> None:
    render_v28_dual_masters.v28_profile = v35_profile
    render_v28_dual_masters.DEFAULT_PRINT_LUT_CACHE = PRINT_LUT
    render_v28_dual_masters.EXPECTED_PRINT_LUT_SHA256 = PRINT_LUT_SHA256
    render_v28_dual_masters.main()


if __name__ == "__main__":
    main()
