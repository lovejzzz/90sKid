#!/usr/bin/env python3
"""Build colour-managed V24 web loops from the untouched 12-bit masters.

The large JPEGs are sRGB review renders of representative frame 12.  This
script applies the same Rec.709-OETF-to-sRGB conversion to every video frame,
rotates the loop so representative frame 12 is first, and verifies that the
decoded first frame remains close to the corresponding large JPEG.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np


WIDTH = 1920
HEIGHT = 1440
FPS = "24000/1001"
FRAME_COUNT = 24
REPRESENTATIVE_FRAME = 12


def transfer_lut() -> np.ndarray:
    encoded = np.arange(65536, dtype=np.float64) / 65535.0
    linear = np.where(
        encoded < 0.081,
        encoded / 4.5,
        np.power((encoded + 0.099) / 1.099, 1.0 / 0.45),
    )
    srgb = np.where(
        linear <= 0.0031308,
        12.92 * linear,
        1.055 * np.power(linear, 1.0 / 2.4) - 0.055,
    )
    return np.rint(np.clip(srgb, 0.0, 1.0) * 255.0).astype(np.uint8)


def decode_master(master: Path, frame_dir: Path, lut: np.ndarray) -> None:
    probe = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,nb_frames",
            "-of", "json", str(master),
        ],
        text=True,
    )
    stream = json.loads(probe)["streams"][0]
    source_width = int(stream["width"])
    source_height = int(stream["height"])
    frame_bytes = source_width * source_height * 3 * 2
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(master), "-an",
            "-f", "rawvideo", "-pix_fmt", "rgb48le", "pipe:1",
        ],
        stdout=subprocess.PIPE,
    )
    assert decoder.stdout is not None
    for index in range(FRAME_COUNT):
        payload = decoder.stdout.read(frame_bytes)
        if len(payload) != frame_bytes:
            raise RuntimeError(f"{master}: decoded {index} frames; expected {FRAME_COUNT}")
        rec709 = np.frombuffer(payload, dtype="<u2").reshape(source_height, source_width, 3)
        srgb = lut[rec709]
        web = cv2.resize(srgb, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA)
        (frame_dir / f"{index:02d}.rgb").write_bytes(web.tobytes())
    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError(f"failed to decode {master}")


def encode_loop(frame_dir: Path, output: Path) -> None:
    encoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
            "-r", FPS, "-i", "pipe:0", "-an",
            "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-tune", "grain", "-crf", "16",
            "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
            "-color_trc", "iec61966-2-1", "-colorspace", "bt709",
            "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=13:matrix_coefficients=1:video_full_range_flag=0",
            "-movflags", "+faststart", str(output),
        ],
        stdin=subprocess.PIPE,
    )
    assert encoder.stdin is not None
    order = list(range(REPRESENTATIVE_FRAME, FRAME_COUNT)) + list(range(REPRESENTATIVE_FRAME))
    for index in order:
        encoder.stdin.write((frame_dir / f"{index:02d}.rgb").read_bytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError(f"failed to encode {output}")


def decoded_first_frame(video: Path) -> np.ndarray:
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(video), "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
        ]
    )
    return np.frombuffer(payload, dtype=np.uint8).reshape(HEIGHT, WIDTH, 3)


def verify(video: Path, reference: Path) -> dict[str, object]:
    first = decoded_first_frame(video).astype(np.float32) / 255.0
    still_bgr = cv2.imread(str(reference), cv2.IMREAD_COLOR)
    if still_bgr is None:
        raise RuntimeError(f"cannot read {reference}")
    still = cv2.cvtColor(still_bgr, cv2.COLOR_BGR2RGB)
    still = cv2.resize(still, (WIDTH, HEIGHT), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    channel_mae = np.mean(np.abs(first - still), axis=(0, 1))
    luma_weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    first_luma = np.sum(first * luma_weights, axis=2)
    still_luma = np.sum(still * luma_weights, axis=2)
    median_delta = float(abs(np.median(first_luma) - np.median(still_luma)))
    if float(np.max(channel_mae)) > 0.025 or median_delta > 0.01:
        raise RuntimeError(
            f"{video.name}: first frame mismatch; channel MAE={channel_mae}, "
            f"median luma delta={median_delta:.6f}"
        )
    probe = json.loads(subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=color_range,color_space,color_transfer,color_primaries",
            "-of", "json", str(video),
        ],
        text=True,
    ))["streams"][0]
    expected_metadata = {
        "color_range": "tv",
        "color_space": "bt709",
        "color_transfer": "iec61966-2-1",
        "color_primaries": "bt709",
    }
    if probe != expected_metadata:
        raise RuntimeError(f"{video.name}: unexpected colour metadata {probe}")
    return {
        "first_frame_channel_mae_rgb": [round(float(value), 6) for value in channel_mae],
        "first_frame_median_luma_delta": round(median_delta, 6),
        "colour_metadata": probe,
    }


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--masters-root",
        type=Path,
        default=site_root.parent / "outputs" / "native_5k_v24_35mm_1s",
    )
    parser.add_argument("--output-dir", type=Path, default=site_root / "public" / "versions")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    jobs = {
        "v24-t020-projection-live-srgb.mp4": ("T020/projection", "v24-t020-projection.jpg"),
        "v24-t020-bluray-live-srgb.mp4": ("T020/bluray_scan", "v24-t020-bluray.jpg"),
        "v24-t032-projection-live-srgb.mp4": ("T032/projection", "v24-t032-projection.jpg"),
        "v24-t032-bluray-live-srgb.mp4": ("T032/bluray_scan", "v24-t032-bluray.jpg"),
    }
    lut = transfer_lut()
    results: dict[str, object] = {}
    for output_name, (relative_master, reference_name) in jobs.items():
        master = args.masters_root / relative_master / "05_emulsion_master_prores4444.mov"
        output = args.output_dir / output_name
        with tempfile.TemporaryDirectory(prefix="v24-web-frames-") as directory:
            frame_dir = Path(directory)
            decode_master(master, frame_dir, lut)
            encode_loop(frame_dir, output)
        results[output_name] = verify(output, args.output_dir / reference_name)
        print(f"built {output_name}: {results[output_name]}", flush=True)

    manifest = {
        "purpose": "V24 colour-managed web proxies; 12-bit Rec.709 masters unchanged",
        "dimensions": [WIDTH, HEIGHT],
        "fps": FPS,
        "frames": FRAME_COUNT,
        "source_transfer": "Rec.709 OETF",
        "web_transfer": "sRGB IEC 61966-2-1",
        "primaries": "Rec.709 / sRGB D65",
        "encoding": "H.264 High, yuv420p, CRF 16, tune grain",
        "first_frame_source_index": REPRESENTATIVE_FRAME,
        "frame_order": list(range(REPRESENTATIVE_FRAME, FRAME_COUNT)) + list(range(REPRESENTATIVE_FRAME)),
        "verification": results,
    }
    (args.output_dir / "v24-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
