#!/usr/bin/env python3
"""Render one V29 frame range through both observers from one emulsion."""

from __future__ import annotations

import render_v28_dual_masters
import v29_profile


def main() -> None:
    # The V28 renderer is deliberately profile-driven.  Substituting the V29
    # evidence contract changes release metadata while retaining the validated
    # image-forming path exactly.
    render_v28_dual_masters.v28_profile = v29_profile
    render_v28_dual_masters.main()


if __name__ == "__main__":
    main()
