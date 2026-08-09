#!/usr/bin/env python3
"""Audit V38's two delivery encodings against one recovered observer light.

The professional file stores inverse-BT.1886 code values and is tagged 1-1-1.
The Mac companion stores sRGB code values and is tagged 1-13-1.  This audit
decodes both back to light after one identical Y'CbCr-to-RGB conversion and
reports the remaining 12-bit ProRes/rounding disagreement.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np


BRANCHES = ("projection", "bluray_scan")
MASTER = "05_emulsion_master_prores4444.mov"
MAC = "06_quicktime_preview_srgb_prores4444.mov"


def probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_streams", "-show_format",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def video_stream(info: dict) -> dict:
    return next(stream for stream in info["streams"] if stream["codec_type"] == "video")


def decode_pipe(path: Path, width: int, height: int) -> subprocess.Popen:
    return subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:v:0",
            # ProRes has no frame-header enum for sRGB, so the companion's
            # bitstream TRC is deliberately reserved while the MOV colr atom
            # remains authoritative.  Give swscale a supported matrix/TRC for
            # the code-value conversion only; transfer is decoded explicitly
            # below, after Y'CbCr has become RGB code values.
            "-vf", (
                "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709,"
                f"scale={width}:{height}:flags=area"
            ), "-pix_fmt", "rgb48le",
            "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )


def read_exact(stream, size: int) -> bytes:
    parts: list[bytes] = []
    remaining = size
    while remaining:
        part = stream.read(remaining)
        if not part:
            break
        parts.append(part)
        remaining -= len(part)
    return b"".join(parts)


def srgb_to_linear(value: np.ndarray) -> np.ndarray:
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4)


def compare_light(master: Path, mac: Path, width: int, height: int, frames: int) -> dict:
    master_pipe = decode_pipe(master, width, height)
    mac_pipe = decode_pipe(mac, width, height)
    assert master_pipe.stdout is not None and mac_pipe.stdout is not None
    frame_bytes = width * height * 3 * 2
    sums = np.zeros(3, np.float64)
    maxima = np.zeros(3, np.float64)
    count = 0
    completed = 0
    try:
        for _ in range(frames):
            master_raw = read_exact(master_pipe.stdout, frame_bytes)
            mac_raw = read_exact(mac_pipe.stdout, frame_bytes)
            if len(master_raw) != frame_bytes or len(mac_raw) != frame_bytes:
                break
            master_code = np.frombuffer(master_raw, "<u2").reshape(height, width, 3).astype(np.float32) / 65535.0
            mac_code = np.frombuffer(mac_raw, "<u2").reshape(height, width, 3).astype(np.float32) / 65535.0
            master_light = np.power(np.clip(master_code, 0.0, 1.0), 2.4)
            mac_light = srgb_to_linear(np.clip(mac_code, 0.0, 1.0))
            delta = np.abs(master_light - mac_light)
            sums += delta.sum(axis=(0, 1), dtype=np.float64)
            maxima = np.maximum(maxima, delta.max(axis=(0, 1)))
            count += width * height
            completed += 1
    finally:
        if master_pipe.stdout:
            master_pipe.stdout.close()
        if mac_pipe.stdout:
            mac_pipe.stdout.close()
        master_rc = master_pipe.wait()
        mac_rc = mac_pipe.wait()
    if master_rc or mac_rc or completed != frames:
        raise RuntimeError(f"decode failed or short: master={master_rc}, mac={mac_rc}, frames={completed}/{frames}")
    return {
        "frames": completed,
        "comparison_size": [width, height],
        "mean_absolute_light_error_rgb": (sums / count).tolist(),
        "maximum_absolute_light_error_rgb": maxima.tolist(),
    }


def validate_metadata(
    path: Path,
    expected_trc: str,
    expected_frames: int,
    expected_profile: str | None = None,
) -> dict:
    info = probe(path)
    video = video_stream(info)
    observed = {
        "width": video.get("width"),
        "height": video.get("height"),
        "pix_fmt": video.get("pix_fmt"),
        "profile": video.get("profile"),
        "frames": int(video.get("nb_frames", 0)),
        "primaries": video.get("color_primaries"),
        "transfer": video.get("color_transfer"),
        "matrix": video.get("color_space"),
        "audio_streams": sum(s.get("codec_type") == "audio" for s in info["streams"]),
        "timecode_streams": sum(s.get("codec_tag_string") == "tmcd" for s in info["streams"]),
    }
    expected = {
        "width": 5760,
        "height": 4320,
        "pix_fmt": "yuv444p12le",
        "frames": expected_frames,
        "primaries": "bt709",
        "transfer": expected_trc,
        "matrix": "bt709",
    }
    failures = {key: [observed[key], value] for key, value in expected.items() if observed[key] != value}
    if expected_profile is not None and observed["profile"] != expected_profile:
        failures["profile"] = [observed["profile"], expected_profile]
    if observed["audio_streams"] < 1:
        failures["audio_streams"] = [observed["audio_streams"], ">=1"]
    if observed["timecode_streams"] < 1:
        failures["timecode_streams"] = [observed["timecode_streams"], ">=1"]
    return {"path": str(path), "observed": observed, "failures": failures}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--scenes", nargs="+", default=["T002", "T007", "T031"])
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument(
        "--master-profile",
        help="Optional ffprobe profile required for the professional master",
    )
    parser.add_argument(
        "--mac-profile",
        help="Optional ffprobe profile required for the sRGB companion (for V39: XQ)",
    )
    parser.add_argument(
        "--contract",
        default="V38 one observer light / two explicit transfer encodings",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "contract": args.contract,
        "scenes": {},
    }
    failed = False
    for scene in args.scenes:
        scene_report = {}
        for branch in BRANCHES:
            base = args.root / scene / branch
            master = base / MASTER
            mac = base / MAC
            master_meta = validate_metadata(
                master, "bt709", args.frames, args.master_profile
            )
            mac_meta = validate_metadata(
                mac, "iec61966-2-1", args.frames, args.mac_profile
            )
            light = compare_light(master, mac, args.width, args.height, args.frames)
            mean_max = max(light["mean_absolute_light_error_rgb"])
            branch_pass = not master_meta["failures"] and not mac_meta["failures"] and mean_max < 0.0015
            failed |= not branch_pass
            scene_report[branch] = {
                "professional_master": master_meta,
                "mac_companion": mac_meta,
                "linear_light_comparison": light,
                "pass": branch_pass,
            }
        report["scenes"][scene] = scene_report
    report["pass"] = not failed
    output = args.output or args.root / "v38_delivery_audit.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
