#!/usr/bin/env python3
"""Render V40 conservative colour-grain repair masters."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import render_v28_dual_masters
import v40_profile


PRINT_LUT = (
    Path(__file__).resolve().parents[1]
    / "cache"
    / "print_2383_monitor_output_lut_193_v30.npy"
)
PRINT_LUT_SHA256 = (
    "5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c"
)


def prores_4444_xq_encoder_command(
    base: Callable[[Path, int, int, str], list[str]],
    path: Path,
    width: int,
    height: int,
    fps: str,
) -> list[str]:
    """Keep the first and only picture authority at 12-bit 4444 XQ quality."""
    command = base(path, width, height, fps)
    command[command.index("-profile:v") + 1] = "5"
    return command


def main() -> None:
    render_v28_dual_masters.v28_profile = v40_profile
    render_v28_dual_masters.DEFAULT_PRINT_LUT_CACHE = PRINT_LUT
    render_v28_dual_masters.EXPECTED_PRINT_LUT_SHA256 = PRINT_LUT_SHA256
    base_encoder = render_v28_dual_masters.e.prores_encoder_command
    render_v28_dual_masters.e.prores_encoder_command = (
        lambda path, width, height, fps: prores_4444_xq_encoder_command(
            base_encoder, path, width, height, fps
        )
    )
    render_v28_dual_masters.main()


if __name__ == "__main__":
    main()
