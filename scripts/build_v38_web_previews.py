#!/usr/bin/env python3
"""Build V38 still/live web media from the sRGB QuickTime companions."""

from __future__ import annotations

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
FRAME_WINDOWS = {"t002": [0, 23], "t007": [276, 299], "t031": [132, 155]}


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


def probe(path: Path) -> dict[str, object]:
    return json.loads(subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries",
            (
                "stream=width,height,nb_frames,pix_fmt,bits_per_raw_sample,"
                "color_space,color_transfer,color_primaries"
            ),
            "-of", "json", str(path),
        ],
        text=True,
    ))["streams"][0]


def decode_companion(
    master: Path,
    frame_dir: Path,
    large_still: Path,
    small_still: Path,
) -> dict[str, object]:
    metadata = probe(master)
    if metadata.get("color_transfer") != "iec61966-2-1":
        raise ValueError(f"{master}: expected sRGB transfer, got {metadata}")
    width, height = int(metadata["width"]), int(metadata["height"])
    frame_bytes = width * height * 3 * 2
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(master), "-an",
            "-vf",
            (
                "setparams=color_primaries=bt709:"
                "color_trc=iec61966-2-1:colorspace=bt709"
            ),
            "-f", "rawvideo", "-pix_fmt", "rgb48le", "pipe:1",
        ],
        stdout=subprocess.PIPE,
    )
    assert decoder.stdout is not None
    for index in range(FRAME_COUNT):
        payload = read_exact(decoder.stdout, frame_bytes)
        if len(payload) != frame_bytes:
            raise RuntimeError(
                f"{master}: decoded {index} frames; expected {FRAME_COUNT}"
            )
        encoded = np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)
        srgb = np.rint(encoded.astype(np.float32) / 257.0).astype(np.uint8)
        video = cv2.resize(srgb, VIDEO_SIZE, interpolation=cv2.INTER_AREA)
        (frame_dir / f"{index:02d}.rgb").write_bytes(video.tobytes())
        if index == REPRESENTATIVE_FRAME:
            large = cv2.resize(srgb, LARGE_SIZE, interpolation=cv2.INTER_AREA)
            small = cv2.resize(srgb, SMALL_SIZE, interpolation=cv2.INTER_AREA)
            cv2.imwrite(
                str(large_still), cv2.cvtColor(large, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 97],
            )
            cv2.imwrite(
                str(small_still), cv2.cvtColor(small, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 93],
            )
    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError(f"failed to decode {master}")
    return metadata


def encode_loop(frame_dir: Path, output: Path) -> None:
    encoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{VIDEO_SIZE[0]}x{VIDEO_SIZE[1]}",
            "-r", FPS, "-i", "pipe:0", "-an",
            "-vf",
            "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-tune", "grain",
            "-crf", "15", "-g", "6", "-keyint_min", "6",
            "-sc_threshold", "0", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "iec61966-2-1",
            "-colorspace", "bt709",
            "-bsf:v",
            (
                "h264_metadata=colour_primaries=1:transfer_characteristics=13:"
                "matrix_coefficients=1:video_full_range_flag=0"
            ),
            "-movflags", "+faststart", str(output),
        ],
        stdin=subprocess.PIPE,
    )
    assert encoder.stdin is not None
    order = list(range(REPRESENTATIVE_FRAME, FRAME_COUNT)) + list(
        range(REPRESENTATIVE_FRAME)
    )
    for index in order:
        encoder.stdin.write((frame_dir / f"{index:02d}.rgb").read_bytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError(f"failed to encode {output}")


def verify(video: Path, still: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(video), "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
        ]
    )
    first = np.frombuffer(payload, np.uint8).reshape(
        VIDEO_SIZE[1], VIDEO_SIZE[0], 3
    ).astype(np.float32) / 255.0
    reference = cv2.cvtColor(cv2.imread(str(still)), cv2.COLOR_BGR2RGB)
    reference = cv2.resize(
        reference, VIDEO_SIZE, interpolation=cv2.INTER_AREA
    ).astype(np.float32) / 255.0
    mae = np.mean(np.abs(first - reference), axis=(0, 1))
    weights = np.array([.2126, .7152, .0722], dtype=np.float32)
    first_luma = np.einsum("...c,c->...", first, weights)
    reference_luma = np.einsum("...c,c->...", reference, weights)
    median_delta = abs(float(np.median(first_luma)) - float(np.median(reference_luma)))
    percentile_deltas = np.abs(
        np.quantile(first_luma, [.05, .5, .95])
        - np.quantile(reference_luma, [.05, .5, .95])
    )
    if float(np.max(mae)) > .018 or float(np.max(percentile_deltas)) > .010:
        raise RuntimeError(
            f"{video.name}: still/live mismatch {mae}, {percentile_deltas}"
        )
    return {
        "first_frame_channel_mae_rgb": [round(float(v), 6) for v in mae],
        "luma_p05_p50_p95_absolute_delta": [
            round(float(v), 6) for v in percentile_deltas
        ],
        "first_frame_median_luma_delta": round(median_delta, 6),
    }


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    root = site_root.parent / "outputs" / "native_5k_v38_reference_delivery_1s"
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}

    for source in ("t002", "t007", "t031"):
        source_upper = source.upper()
        for branch_name, directory in (
            ("projection", "projection"), ("bluray", "bluray_scan")
        ):
            master = (
                root / source_upper / directory
                / "06_quicktime_preview_srgb_prores4444.mov"
            )
            stem = f"v38-{source}-{branch_name}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
                metadata = decode_companion(
                    master, Path(temporary), large, small
                )
                encode_loop(Path(temporary), video)
            results[stem] = {
                "absolute_source_frames": FRAME_WINDOWS[source],
                "quicktime_companion": str(master),
                "companion_metadata": metadata,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

    manifest = {
        "purpose": "V38 single-observer-light delivery consistency release",
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "absolute_source_frame_contract": FRAME_WINDOWS,
        "film_pipeline": "V37 frozen byte-for-byte before delivery encoding",
        "professional_master": "Rec.709 / inverse BT.1886 gamma 2.4 / 12-bit ProRes 4444",
        "quicktime_companion": "Rec.709 primaries / IEC sRGB transfer / 12-bit ProRes 4444",
        "web": "decoded directly from the sRGB companion; no second OETF inversion",
        "proxy_encoding": "H.264 High / yuv420p / CRF 15 / tune grain / closed GOP 6",
        "verification": results,
    }
    (assets / "v38-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
