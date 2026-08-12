#!/usr/bin/env python3
"""Build V49 web witnesses without reintroducing visible chroma noise."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from build_v38_web_previews import FRAME_COUNT, FPS, REPRESENTATIVE_FRAME, SMALL_SIZE, probe, read_exact
from build_v44_web_previews import public_value, sha256


WEB_SIZE = (1920, 1440)


def decode_review(review: Path, frame_dir: Path, large: Path, small: Path) -> dict[str, object]:
    metadata = probe(review)
    if metadata.get("color_transfer") != "iec61966-2-1":
        raise ValueError(f"{review}: expected an sRGB review authority")
    width, height = int(metadata["width"]), int(metadata["height"])
    if (width, height) != WEB_SIZE:
        raise ValueError(f"{review}: expected {WEB_SIZE}, got {(width, height)}")
    size = width * height * 3 * 2
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(review), "-an", "-frames:v", str(FRAME_COUNT),
            "-vf", "setparams=color_primaries=bt709:color_trc=iec61966-2-1:colorspace=bt709",
            "-f", "rawvideo", "-pix_fmt", "rgb48le", "pipe:1",
        ],
        stdout=subprocess.PIPE,
    )
    if decoder.stdout is None:
        raise RuntimeError("failed to open review decoder")
    for index in range(FRAME_COUNT):
        payload = read_exact(decoder.stdout, size)
        if len(payload) != size:
            raise RuntimeError(f"{review}: decoded {index}/{FRAME_COUNT} frames")
        encoded = np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)
        srgb = np.rint(encoded.astype(np.float32) / 257.0).astype(np.uint8)
        (frame_dir / f"{index:02d}.rgb").write_bytes(srgb.tobytes())
        if index == REPRESENTATIVE_FRAME:
            Image.fromarray(srgb, mode="RGB").save(large, quality=98, subsampling=0)
            thumb = cv2.resize(srgb, SMALL_SIZE, interpolation=cv2.INTER_AREA)
            Image.fromarray(thumb, mode="RGB").save(small, quality=94, subsampling=0)
    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError(f"failed to decode {review}")
    return metadata


def encode_web(frame_dir: Path, output: Path) -> None:
    encoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{WEB_SIZE[0]}x{WEB_SIZE[1]}", "-r", FPS, "-i", "pipe:0", "-an",
            "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv444p",
            "-c:v", "libx264", "-profile:v", "high444", "-preset", "slow", "-tune", "grain", "-crf", "10",
            "-g", "6", "-keyint_min", "6", "-sc_threshold", "0", "-pix_fmt", "yuv444p",
            "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-colorspace", "bt709",
            "-bsf:v", "h264_metadata=colour_primaries=1:transfer_characteristics=13:matrix_coefficients=1:video_full_range_flag=0",
            "-movflags", "+faststart", str(output),
        ],
        stdin=subprocess.PIPE,
    )
    if encoder.stdin is None:
        raise RuntimeError("failed to open web encoder")
    order = list(range(REPRESENTATIVE_FRAME, FRAME_COUNT)) + list(range(REPRESENTATIVE_FRAME))
    for index in order:
        encoder.stdin.write((frame_dir / f"{index:02d}.rgb").read_bytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError(f"failed to encode {output}")


def decode_review_frame(review: Path) -> np.ndarray:
    payload = subprocess.check_output(
        [
            "ffmpeg", "-v", "error", "-i", str(review),
            "-vf", f"select=eq(n\\,{REPRESENTATIVE_FRAME}),setparams=color_primaries=bt709:color_trc=iec61966-2-1:colorspace=bt709",
            "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
        ]
    )
    return np.frombuffer(payload, np.uint8).reshape(WEB_SIZE[1], WEB_SIZE[0], 3).astype(np.float32) / 255.0


def residual_metrics(candidate: np.ndarray, reference: np.ndarray) -> dict[str, object]:
    delta = candidate - reference
    opponent = delta - np.mean(delta, axis=2, keepdims=True)
    channel_mae = np.mean(np.abs(delta), axis=(0, 1))
    return {
        "channel_mae_rgb": [round(float(value), 6) for value in channel_mae],
        "opponent_rms": round(float(np.sqrt(np.mean(opponent * opponent))), 6),
        "opponent_p999": round(float(np.quantile(np.max(np.abs(opponent), axis=2), 0.999)), 6),
    }


def verify_web(video: Path, still: Path, review: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", str(video), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    )
    live = np.frombuffer(payload, np.uint8).reshape(WEB_SIZE[1], WEB_SIZE[0], 3).astype(np.float32) / 255.0
    still_frame = np.asarray(Image.open(still).convert("RGB"), dtype=np.float32) / 255.0
    reference = decode_review_frame(review)
    live_metrics = residual_metrics(live, reference)
    still_metrics = residual_metrics(still_frame, reference)
    extra_opponent_rms = max(0.0, float(live_metrics["opponent_rms"]) - float(still_metrics["opponent_rms"]))
    extra_opponent_p999 = max(0.0, float(live_metrics["opponent_p999"]) - float(still_metrics["opponent_p999"]))
    if extra_opponent_rms > 0.0010 or extra_opponent_p999 > 0.005:
        raise RuntimeError(
            f"{video.name}: video adds more chroma error than the still; "
            f"extra_rms={extra_opponent_rms}, extra_p999={extra_opponent_p999}"
        )
    return {
        "video_vs_review": live_metrics,
        "still_vs_review": still_metrics,
        "video_extra_opponent_rms_over_still": round(extra_opponent_rms, 6),
        "video_extra_opponent_p999_over_still": round(extra_opponent_p999, 6),
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    release = root / "outputs/native_5k_v49_common_density_1s/T020"
    assets = root / "public/versions"
    results: dict[str, object] = {}
    for branch, directory in (("projection", "projection"), ("bluray", "bluray_scan")):
        review = release / directory / "07_scale_integrated_review_srgb_prores4444.mov"
        stem = f"v49-t020-{branch}"
        large = assets / f"{stem}.jpg"
        small = assets / f"{stem}-sm.jpg"
        video = assets / f"{stem}-live-srgb.mp4"
        with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
            metadata = decode_review(review, Path(temporary), large, small)
            encode_web(Path(temporary), video)
        results[stem] = {
            "review_sha256": sha256(review),
            "review_metadata": metadata,
            **verify_web(video, large, review),
        }
        print(f"built {stem}", flush=True)

    source = cv2.imread(str(assets / "v49-t020-projection.jpg"))
    crop_height = round(source.shape[1] / (1731 / 909))
    crop_y = (source.shape[0] - crop_height) // 2
    social = cv2.resize(source[crop_y:crop_y + crop_height], (1731, 909), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(root / "public/og-v49.png"), social)

    manifest = {
        "release": "V49 Conservative Common-Density Formation",
        "release_class": "conservative_common_density_joint_law_boundary",
        "frames": FRAME_COUNT,
        "dimensions": list(WEB_SIZE),
        "representative_frame": REPRESENTATIVE_FRAME,
        "web_authority": "still and motion decoded from the same encoded 1920x1440 sRGB review",
        "proxy_encoding": "H.264 High 4:4:4 / 1920x1440 / yuv444p / CRF 10 / tune grain",
        "image_change": "common negative density before both material observers; no display-RGB grain reinjection",
        "crop_ab_audit": public_value(json.loads((root / "engine/research_runs/v49_public_common_density_t020_crop/audit.json").read_text())),
        "timing": public_value(json.loads((release / "timing.json").read_text())),
        "verification": results,
    }
    (assets / "v49-live-preview-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
