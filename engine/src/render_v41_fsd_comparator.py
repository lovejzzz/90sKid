#!/usr/bin/env python3
"""Render V41 deterministic and FSD controls beside the physical model."""

from __future__ import annotations

import render_v40_fsd_comparator as renderer
import v41_profile


def main() -> None:
    renderer.v40_profile = v41_profile
    renderer.main()


if __name__ == "__main__":
    main()
