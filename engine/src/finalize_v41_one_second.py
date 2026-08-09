#!/usr/bin/env python3
"""Finalize V41 viewing copies, source audio and timecode."""

from __future__ import annotations

import sys

import finalize_v40_one_second


def main() -> None:
    if "--release-id" not in sys.argv:
        sys.argv.extend(["--release-id", "V41"])
    finalize_v40_one_second.main()


if __name__ == "__main__":
    main()
