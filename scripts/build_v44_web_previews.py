#!/usr/bin/env python3
"""Build V44 web media from the scale-integrated encoded review authority."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from build_v38_web_previews import (
    FRAME_COUNT,
    FPS,
    REPRESENTATIVE_FRAME,
    SMALL_SIZE,
    VIDEO_SIZE,
    encode_loop,
    probe,
    read_exact,
    verify,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def public_value(value: object) -> object:
    if isinstance(value, dict):
        return {key: public_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_value(item) for item in value]
    if isinstance(value, str) and value.startswith("/"):
        return Path(value).name
    return value


def decode_review(
    review: Path,
    frame_dir: Path,
    large_still: Path,
    small_still: Path,
) -> dict[str, object]:
    """Use the encoded 1920 review for both motion and still assets."""

    metadata = probe(review)
    if metadata.get("color_transfer") != "iec61966-2-1":
        raise ValueError(f"{review}: expected sRGB transfer, got {metadata}")
    width, height = int(metadata["width"]), int(metadata["height"])
    if (width, height) != (1920, 1440):
        raise ValueError(f"{review}: expected 1920x1440 review authority")
    frame_bytes = width * height * 3 * 2
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(review), "-an",
            "-vf",
            (
                "setparams=color_primaries=bt709:"
                "color_trc=iec61966-2-1:colorspace=bt709"
            ),
            "-frames:v", str(FRAME_COUNT),
            "-f", "rawvideo", "-pix_fmt", "rgb48le", "pipe:1",
        ],
        stdout=subprocess.PIPE,
    )
    if decoder.stdout is None:
        raise RuntimeError("failed to open V44 review decoder")
    for index in range(FRAME_COUNT):
        payload = read_exact(decoder.stdout, frame_bytes)
        if len(payload) != frame_bytes:
            raise RuntimeError(
                f"{review}: decoded {index} frames; expected {FRAME_COUNT}"
            )
        encoded = np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)
        srgb = np.rint(encoded.astype(np.float32) / 257.0).astype(np.uint8)
        video = cv2.resize(srgb, VIDEO_SIZE, interpolation=cv2.INTER_AREA)
        (frame_dir / f"{index:02d}.rgb").write_bytes(video.tobytes())
        if index == REPRESENTATIVE_FRAME:
            if not cv2.imwrite(
                str(large_still),
                cv2.cvtColor(srgb, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 97],
            ):
                raise RuntimeError(f"failed to write {large_still}")
            small = cv2.resize(srgb, SMALL_SIZE, interpolation=cv2.INTER_AREA)
            if not cv2.imwrite(
                str(small_still),
                cv2.cvtColor(small, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 93],
            ):
                raise RuntimeError(f"failed to write {small_still}")
    decoder.stdout.close()
    if decoder.wait() != 0:
        raise RuntimeError(f"failed to decode {review}")
    return metadata


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    release = site_root / "outputs" / "native_5k_v44_scale_honest_release_1s"
    scene = release / "T020"
    assets = site_root / "public" / "versions"
    results: dict[str, object] = {}

    for branch, directory in (("projection", "projection"), ("bluray", "bluray_scan")):
        review = (
            scene / directory / "07_scale_integrated_review_srgb_prores4444.mov"
        )
        stem = f"v44-t020-{branch}"
        large = assets / f"{stem}.jpg"
        small = assets / f"{stem}-sm.jpg"
        video = assets / f"{stem}-live-srgb.mp4"
        with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
            metadata = decode_review(review, Path(temporary), large, small)
            encode_loop(Path(temporary), video)
        results[stem] = {
            "absolute_source_frames": [0, 23],
            "native_master": f"T020/{directory}/05_emulsion_master_prores4444.mov",
            "scale_integrated_review": (
                f"T020/{directory}/"
                "07_scale_integrated_review_srgb_prores4444.mov"
            ),
            "review_sha256": sha256(review),
            "review_metadata": metadata,
            **verify(video, large),
        }
        print(f"built {stem}", flush=True)

    social_source = cv2.imread(str(assets / "v44-t020-projection.jpg"))
    if social_source is None:
        raise RuntimeError("failed to read V44 projection still for social image")
    target_ratio = 1731 / 909
    crop_height = round(social_source.shape[1] / target_ratio)
    crop_y = (social_source.shape[0] - crop_height) // 2
    social_crop = social_source[crop_y : crop_y + crop_height]
    social = cv2.resize(social_crop, (1731, 909), interpolation=cv2.INTER_AREA)
    if not cv2.imwrite(str(site_root / "public" / "og-v44.png"), social):
        raise RuntimeError("failed to write V44 social image")

    timing = public_value(json.loads((scene / "timing.json").read_text()))
    audit = public_value(json.loads(
        (release / "v44_motion_colour_grain_audit.json").read_text()
    ))
    manifest = {
        "release": "V44 observer integrity and scale-honest review",
        "release_class": "evidence_boundary_revision",
        "image_formation": "accepted V42 profile; V43H hypotheses withdrawn",
        "projection_colour": (
            "accepted V31 normal-process monitor boundary: 2383 lightness and "
            "texture with low-frequency scan-referenced dye chroma"
        ),
        "display_review": (
            "encoded native BT.1886 master → linear observer light → "
            "1920x1440 pixel-area integration → sRGB ProRes XQ"
        ),
        "web": (
            "decoded only from the encoded scale-integrated review; hover "
            "frame zero and JPEG share review frame 12"
        ),
        "dimensions": list(VIDEO_SIZE),
        "large_still_dimensions": [1920, 1440],
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "proxy_encoding": (
            "H.264 High / yuv420p / CRF 18 / tune grain / closed GOP 6"
        ),
        "timing": timing,
        "native_release_audit": audit,
        "verification": results,
    }
    (assets / "v44-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
