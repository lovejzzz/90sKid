#!/usr/bin/env python3
"""Run the V31 profile-placement probe (rejected as the release path).

Full-frame regression showed that a downstream legacy hybrid branch largely
bypassed this cached-LUT change.  Production V31 masters are made by
``apply_v31_normal_process_adapter.py`` after both complete V30 observers.
"""

from __future__ import annotations

from pathlib import Path

import render_v28_dual_masters
import v31_profile


V31_PRINT_LUT = (
    Path(__file__).resolve().parents[1]
    / "cache"
    / "print_2383_monitor_output_lut_193_v31.npy"
)
V31_PRINT_LUT_SHA256 = (
    "be4a5a631c462c961983a6a00725b96df9e115fbe9b4c68bc39e92c53216d081"
)


def main() -> None:
    render_v28_dual_masters.v28_profile = v31_profile
    render_v28_dual_masters.DEFAULT_PRINT_LUT_CACHE = V31_PRINT_LUT
    render_v28_dual_masters.EXPECTED_PRINT_LUT_SHA256 = V31_PRINT_LUT_SHA256
    render_v28_dual_masters.main()


if __name__ == "__main__":
    main()
