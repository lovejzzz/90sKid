#!/usr/bin/env python3
"""Build matched sRGB still/live proxies from a numbered display-master release."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np


VIDEO_SIZE = (1920, 1440)
LARGE_SIZE = (2560, 1920)
SMALL_SIZE = (800, 600)
FPS = "24000/1001"
FRAME_COUNT = 24
REPRESENTATIVE_FRAME = 12
def srgb_encode(linear: np.ndarray) -> np.ndarray:
    linear = np.clip(linear, 0.0, 1.0)
    return np.where(
        linear <= .0031308,
        12.92 * linear,
        1.055 * np.power(linear, 1 / 2.4) - .055,
    )


def rec709_decode(encoded: np.ndarray) -> np.ndarray:
    encoded = np.clip(encoded, 0.0, 1.0)
    return np.where(
        encoded < .081,
        encoded / 4.5,
        np.power((encoded + .099) / 1.099, 1 / .45),
    )


def master_signal_to_srgb(signal: np.ndarray, branch: str) -> np.ndarray:
    encoded = signal.astype(np.float32) / 65535.0
    if branch not in {"projection", "bluray"}:
        raise ValueError(branch)
    linear = rec709_decode(encoded)
    return np.rint(srgb_encode(linear) * 255.0).astype(np.uint8)


def decode_master(
    master: Path,
    branch: str,
    frame_dir: Path,
    large_still: Path,
    small_still: Path,
) -> dict[str, object]:
    probe = json.loads(subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,nb_frames,pix_fmt,bits_per_raw_sample,color_space,color_transfer,color_primaries",
            "-of", "json", str(master),
        ], text=True,
    ))["streams"][0]
    width, height = int(probe["width"]), int(probe["height"])
    frame_bytes = width * height * 3 * 2
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(master), "-an",
            # Both masters carry complete Rec.709 1-1-1 signalling. Decode the
            # interchange OETF explicitly before the browser sRGB transform.
            "-vf", "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
            "-f", "rawvideo", "-pix_fmt", "rgb48le", "pipe:1",
        ],
        stdout=subprocess.PIPE,
    )
    assert decoder.stdout is not None
    for index in range(FRAME_COUNT):
        payload = decoder.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            raise RuntimeError(f"{master}: decoded {index} frames; expected {FRAME_COUNT}")
        signal = np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)
        srgb = master_signal_to_srgb(signal, branch)
        video = cv2.resize(srgb, VIDEO_SIZE, interpolation=cv2.INTER_AREA)
        (frame_dir / f"{index:02d}.rgb").write_bytes(video.tobytes())
        if index == REPRESENTATIVE_FRAME:
            large = cv2.resize(srgb, LARGE_SIZE, interpolation=cv2.INTER_AREA)
            small = cv2.resize(srgb, SMALL_SIZE, interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(large_still), cv2.cvtColor(large, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 96])
            cv2.imwrite(str(small_still), cv2.cvtColor(small, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 91])
    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError(f"failed to decode {master}")
    return probe


def encode_loop(frame_dir: Path, output: Path) -> None:
    encoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{VIDEO_SIZE[0]}x{VIDEO_SIZE[1]}", "-r", FPS, "-i", "pipe:0", "-an",
            "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p",
            # The browser proxy is a hover preview, not the archive master.
            # CRF 20 with grain tuning preserves the moving texture while
            # keeping the cumulative version archive within its hosting cap.
            "-c:v", "libx264", "-preset", "slow", "-tune", "grain", "-crf", "20",
            "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
            "-color_trc", "iec61966-2-1", "-colorspace", "bt709",
            "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=13:matrix_coefficients=1:video_full_range_flag=0",
            "-movflags", "+faststart", str(output),
        ], stdin=subprocess.PIPE,
    )
    assert encoder.stdin is not None
    order = list(range(REPRESENTATIVE_FRAME, FRAME_COUNT)) + list(range(REPRESENTATIVE_FRAME))
    for index in order:
        encoder.stdin.write((frame_dir / f"{index:02d}.rgb").read_bytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError(f"failed to encode {output}")


def verify(video: Path, still: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", str(video), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    )
    first = np.frombuffer(payload, np.uint8).reshape(VIDEO_SIZE[1], VIDEO_SIZE[0], 3).astype(np.float32) / 255
    reference = cv2.cvtColor(cv2.imread(str(still)), cv2.COLOR_BGR2RGB)
    reference = cv2.resize(reference, VIDEO_SIZE, interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    mae = np.mean(np.abs(first - reference), axis=(0, 1))
    weights = np.array([.2126, .7152, .0722], dtype=np.float32)
    first_luma = np.einsum("...c,c->...", first, weights)
    reference_luma = np.einsum("...c,c->...", reference, weights)
    median_delta = abs(float(np.median(first_luma)) - float(np.median(reference_luma)))
    if not np.all(np.isfinite(mae)) or not np.isfinite(median_delta):
        raise RuntimeError(f"{video.name}: non-finite still/live validation")
    if float(np.max(mae)) > .025 or median_delta > .01:
        raise RuntimeError(f"{video.name}: still/live mismatch {mae}, {median_delta}")
    return {"first_frame_channel_mae_rgb": [round(float(v), 6) for v in mae], "first_frame_median_luma_delta": round(median_delta, 6)}


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v25")
    parser.add_argument("--masters-root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=site_root / "public" / "versions")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    version = args.version.lower()
    masters_root = args.masters_root or (
        site_root.parent / "outputs" / f"native_5k_{version}_corrected_1s"
    )
    jobs = {
        f"{version}-t020-projection": ("T020/projection", "projection"),
        f"{version}-t020-bluray": ("T020/bluray_scan", "bluray"),
        f"{version}-t032-projection": ("T032/projection", "projection"),
        f"{version}-t032-bluray": ("T032/bluray_scan", "bluray"),
    }
    results: dict[str, object] = {}
    for stem, (relative, branch) in jobs.items():
        master = masters_root / relative / "05_emulsion_master_prores4444.mov"
        large, small = args.output_dir / f"{stem}.jpg", args.output_dir / f"{stem}-sm.jpg"
        video = args.output_dir / f"{stem}-live-srgb.mp4"
        with tempfile.TemporaryDirectory(prefix=f"{version}-web-") as directory:
            probe = decode_master(master, branch, Path(directory), large, small)
            encode_loop(Path(directory), video)
        results[stem] = {"master_metadata": probe, **verify(video, large)}
        print(f"built {stem}", flush=True)
    manifest = {
        "purpose": f"{version.upper()} corrected Rec.709-to-sRGB web proxies from 12-bit masters",
        "dimensions": list(VIDEO_SIZE), "fps": FPS, "frames": FRAME_COUNT,
        "first_frame_source_index": REPRESENTATIVE_FRAME,
        "projection_source": "Rec.709-D65 1-1-1 monitor rendering of the 48-nit gamma-2.6 cinema observer",
        "bluray_source": "Rec.709-D65 1-1-1 Blu-ray rendering; BT.1886 is the reference display EOTF",
        "web": "sRGB IEC 61966-2-1; no browser-dependent master interpretation",
        "proxy_encoding": "H.264 High / yuv420p / CRF 20 / tune grain; archive masters remain 5.7K 12-bit ProRes 4444",
        "verification": results,
    }
    (args.output_dir / f"{version}-live-preview-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
