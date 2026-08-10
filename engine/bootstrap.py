#!/usr/bin/env python3
"""Build local runtime assets and fetch optional official research LUTs."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from emulsion5279.assets import (  # noqa: E402
    PANASONIC_RAW_GAMUT,
    PANASONIC_V709,
    PRINT_2383_OUTPUT_LATTICE,
    PRINT_2383_OUTPUT_LATTICE_V45,
)


PANASONIC_RAW_URL = (
    "https://av.jpn.support.panasonic.com/support/share2/eww/com/dsc/lut/"
    "VLog_RAWGamut_to_VLog_VGamut_forS1H_ver100.cube"
)
PANASONIC_V709_ZIP_URL = (
    "https://av.jpn.support.panasonic.com/support/share2/eww/en/dsc/lut/"
    "VLog_to_V709_forV35_EN.zip"
)


def download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, output.open("wb") as stream:
        stream.write(response.read())


def build_runtime() -> None:
    PRINT_2383_OUTPUT_LATTICE.path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            str(SRC / "build_v30_print_lut.py"),
            str(PRINT_2383_OUTPUT_LATTICE.path),
        ],
        check=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(SRC)},
    )
    PRINT_2383_OUTPUT_LATTICE.verify()
    subprocess.run(
        [
            sys.executable,
            str(SRC / "build_v45_print_lut.py"),
            str(PRINT_2383_OUTPUT_LATTICE_V45.path),
        ],
        check=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(SRC)},
    )
    PRINT_2383_OUTPUT_LATTICE_V45.verify()


def fetch_research() -> None:
    import tempfile
    import zipfile

    download(PANASONIC_RAW_URL, PANASONIC_RAW_GAMUT.path)
    PANASONIC_RAW_GAMUT.verify()
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "v709.zip"
        download(PANASONIC_V709_ZIP_URL, archive)
        with zipfile.ZipFile(archive) as bundle:
            payload = bundle.read(
                "VLog_to_V709_forV35_EN/VLog_to_V709_forV35_ver100.cube"
            )
        PANASONIC_V709.path.parent.mkdir(parents=True, exist_ok=True)
        PANASONIC_V709.path.write_bytes(payload)
    PANASONIC_V709.verify()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--research",
        action="store_true",
        help="also fetch Panasonic's checksum-locked diagnostic LUTs",
    )
    args = parser.parse_args()
    build_runtime()
    if args.research:
        fetch_research()
    print("5279 engine assets verified")


if __name__ == "__main__":
    main()
