#!/usr/bin/env python3
"""Audit V68's independent Cineon printing-density DPX delivery."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

import numpy as np


def decoded_master_md5(path: Path) -> str:
    output = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0",
            "-frames:v", "1", "-pix_fmt", "yuv444p12le", "-f", "md5", "-",
        ],
        text=True,
    ).strip()
    return output.removeprefix("MD5=")


def audit_dpx(path: Path) -> dict[str, object]:
    with path.open("rb") as stream:
        header = stream.read(1664)
    endian = ">" if header[:4] == b"SDPX" else "<"
    if header[:4] not in (b"SDPX", b"XPDS"):
        raise RuntimeError("invalid DPX magic")
    image_offset = struct.unpack_from(endian + "I", header, 4)[0]
    width = struct.unpack_from(endian + "I", header, 772)[0]
    height = struct.unpack_from(endian + "I", header, 776)[0]
    decoded = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-frames:v", "1",
            "-pix_fmt", "gbrp10le", "-f", "rawvideo", "-",
        ]
    )
    planes = np.frombuffer(decoded, "<u2").reshape(3, height, width)
    rgb = np.stack((planes[2], planes[0], planes[1]), axis=-1)
    with path.open("rb") as stream:
        stream.seek(image_offset)
        packed = np.frombuffer(
            stream.read(), dtype=(">u4" if endian == ">" else "<u4")
        )
    unpacked = np.empty((height * width, 3), dtype=np.uint16)
    unpacked[:, 0] = (packed >> 22) & 1023
    unpacked[:, 1] = (packed >> 12) & 1023
    unpacked[:, 2] = (packed >> 2) & 1023
    flat = rgb.reshape(-1, 3)
    return {
        "path": str(path),
        "file_bytes": path.stat().st_size,
        "dimensions": [width, height],
        "image_offset": image_offset,
        "reference_low": {
            "code": struct.unpack_from(endian + "I", header, 784)[0],
            "density": struct.unpack_from(endian + "f", header, 788)[0],
        },
        "reference_high": {
            "code": struct.unpack_from(endian + "I", header, 792)[0],
            "density": struct.unpack_from(endian + "f", header, 796)[0],
        },
        "descriptor": header[800],
        "transfer_characteristic": header[801],
        "colorimetric_specification": header[802],
        "bit_depth": header[803],
        "packing": struct.unpack_from(endian + "H", header, 804)[0],
        "ffmpeg_decode_matches_packed_words": bool(
            np.array_equal(flat, unpacked)
        ),
        "raw_gbrp10_md5": hashlib.md5(decoded).hexdigest(),
        "code_min_rgb": flat.min(axis=0).tolist(),
        "code_median_rgb": np.median(flat, axis=0).tolist(),
        "code_max_rgb": flat.max(axis=0).tolist(),
        "fraction_at_or_below_reference_black_rgb": np.mean(
            flat <= 95, axis=0
        ).tolist(),
        "fraction_at_code_1023_rgb": np.mean(flat == 1023, axis=0).tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("delivery", type=Path)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = {
        branch: decoded_master_md5(
            args.delivery / branch / "05_emulsion_master_prores4444.mov"
        )
        for branch in ("projection", "bluray_scan")
    }
    reference = {
        branch: decoded_master_md5(
            args.reference / branch / "05_emulsion_master_prores4444.mov"
        )
        for branch in ("projection", "bluray_scan")
    }
    dpx_files = sorted((args.delivery / "cineon_printing_density").glob("*.dpx"))
    if len(dpx_files) != 1:
        raise RuntimeError(f"expected one audit DPX, found {len(dpx_files)}")
    dpx = audit_dpx(dpx_files[0])
    report = {
        "audit": "V68 independent Cineon printing-density DPX delivery",
        "classification": "delivery contract; no image-model revision",
        "source_authorities": [
            {
                "name": "SMPTE ST 268-1:2014",
                "url": "https://pub.smpte.org/latest/st268-1/st0268-1-2014_stable2015.pdf",
                "facts": [
                    "DPX does not define input, output, or display device characteristics.",
                    "Printing-density transfer and colorimetry are code 1.",
                    "10-bit defaults are code 0 = density 0.00 and code 1023 = density 2.048.",
                ],
            },
            {
                "name": "Kodak Cineon file-format description",
                "url": "https://www.kodak.com/content/products-brochures/Film/Cineon-File-Format-Description.pdf",
                "facts": [
                    "Printing density is the exchange metric.",
                    "Code 95 is the conventional reference-black aim.",
                ],
            },
        ],
        "display_master_decoded_md5": current,
        "reference_v66_decoded_md5": reference,
        "display_masters_unchanged": current == reference,
        "dpx": dpx,
        "pass": bool(
            current == reference
            and dpx["ffmpeg_decode_matches_packed_words"]
            and dpx["descriptor"] == 50
            and dpx["transfer_characteristic"] == 1
            and dpx["colorimetric_specification"] == 1
            and dpx["bit_depth"] == 10
            and dpx["packing"] == 1
            and dpx["reference_low"]["code"] == 0
            and dpx["reference_high"]["code"] == 1023
        ),
        "interpretation": (
            "The DPX is scene-independent printing-density exchange data from "
            "the same formed negative and Spirit aperture that feed the scan "
            "observer. It is not a Rec.709 picture and carries no Blu-ray finish."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
