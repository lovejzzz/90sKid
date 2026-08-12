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
    PRINT_2383_OUTPUT_LATTICE_V51,
    PRINT_2383_OUTPUT_LATTICE_V53,
    PRINT_2383_OUTPUT_LATTICE_V54,
    PRINT_2383_OUTPUT_LATTICE_V55,
    PRINT_2383_OUTPUT_LATTICE_V56,
    PRINT_2383_OUTPUT_LATTICE_V57,
    PRINT_2383_OUTPUT_LATTICE_V58,
    PRINT_2383_OUTPUT_LATTICE_V59,
    PRINT_2383_OUTPUT_LATTICE_V60,
    PRINT_2383_OUTPUT_LATTICE_V62,
    PRINT_2383_OUTPUT_LATTICE_V63,
    PRINT_2383_OUTPUT_LATTICE_V64,
    PRINT_2383_OUTPUT_LATTICE_V66,
    verify_v46_runtime_assets,
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
    builders = (
        ("build_v30_print_lut.py", PRINT_2383_OUTPUT_LATTICE),
        ("build_v45_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V45),
        ("build_v51_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V51),
        ("build_v53_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V53),
        ("build_v54_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V54),
        ("build_v55_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V55),
        ("build_v56_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V56),
        ("build_v57_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V57),
        ("build_v58_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V58),
        ("build_v59_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V59),
        ("build_v60_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V60),
        ("build_v62_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V62),
        ("build_v63_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V63),
        ("build_v64_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V64),
        ("build_v66_print_lut.py", PRINT_2383_OUTPUT_LATTICE_V66),
    )
    PRINT_2383_OUTPUT_LATTICE.path.parent.mkdir(parents=True, exist_ok=True)
    environment = {**dict(__import__("os").environ), "PYTHONPATH": str(SRC)}
    for builder, asset in builders:
        subprocess.run(
            [sys.executable, str(SRC / builder), str(asset.path)],
            check=True,
            env=environment,
        )
        asset.verify()


def build_v46_adaptive_observer() -> None:
    """Rebuild the large V46 atlas from versioned code and cell demand."""

    cache = ROOT / "cache"
    research = ROOT / "research_runs"
    candidate = cache / "v46_active_set_129_power2_candidate"
    adaptive = cache / "v46_adaptive_129_power2"
    environment = {**dict(__import__("os").environ), "PYTHONPATH": str(SRC)}
    subprocess.run(
        [
            sys.executable,
            str(SRC / "build_v46_active_set_printer_lut.py"),
            str(candidate),
            "--size", "129",
            "--iterations", "6",
            "--axis-power", "2",
        ],
        check=True,
        env=environment,
    )
    subprocess.run(
        [
            sys.executable,
            str(SRC / "build_v46_adaptive_spectral_cache.py"),
            "base",
            str(candidate.with_name(candidate.name + "_printer.npy")),
            str(candidate.with_name(candidate.name + "_residual.npy")),
            str(candidate.with_name(candidate.name + "_axis.npy")),
            str(adaptive),
        ],
        check=True,
        env=environment,
    )
    subprocess.run(
        [
            sys.executable,
            str(SRC / "build_v46_adaptive_spectral_cache.py"),
            "microbricks",
            str(adaptive.with_name(adaptive.name + "_node_mask.npy")),
            str(adaptive.with_name(adaptive.name + "_axis.npy")),
            str(adaptive),
            str(research / "v46_microbrick_cells_T020_exact_pixels.npy"),
            str(research / "v46_microbrick_cells_T032_exact_pixels.npy"),
            str(research / "v46_microbrick_cells_T007_exact_pixels.npy"),
            str(research / "v46_pipeline_stage_missing_cells.npy"),
            "--iterations", "6",
        ],
        check=True,
        env=environment,
    )
    verify_v46_runtime_assets()


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
    parser.add_argument(
        "--v46",
        action="store_true",
        help="also rebuild the large V46 adaptive spectral-observer cache",
    )
    args = parser.parse_args()
    build_runtime()
    if args.v46:
        build_v46_adaptive_observer()
    if args.research:
        fetch_research()
    print("5279 engine assets verified")


if __name__ == "__main__":
    main()
