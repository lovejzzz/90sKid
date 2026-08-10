#!/usr/bin/env python3
"""Build V45 web media from each encoded scale-integrated review authority."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import cv2

from build_v38_web_previews import (
    FRAME_COUNT,
    FPS,
    REPRESENTATIVE_FRAME,
    VIDEO_SIZE,
    encode_loop,
    verify,
)
from build_v44_web_previews import decode_review, public_value, sha256


SCENES = {
    "t020": ("T020", [0, 23]),
    "t032": ("T032", [0, 23]),
    "t007": ("T007", [276, 299]),
}


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    release = site_root / "outputs" / "native_5k_v45_official_cie_1nm_1s"
    assets = site_root / "public" / "versions"
    results: dict[str, object] = {}
    timings: dict[str, object] = {}

    for scene_key, (scene_dir, source_range) in SCENES.items():
        scene = release / scene_dir
        timings[scene_dir] = public_value(
            json.loads((scene / "timing.json").read_text())
        )
        for branch, directory in (("projection", "projection"), ("bluray", "bluray_scan")):
            review = scene / directory / "07_scale_integrated_review_srgb_prores4444.mov"
            stem = f"v45-{scene_key}-{branch}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
                metadata = decode_review(review, Path(temporary), large, small)
                encode_loop(Path(temporary), video)
            results[stem] = {
                "absolute_source_frames": source_range,
                "native_master": f"{scene_dir}/{directory}/05_emulsion_master_prores4444.mov",
                "scale_integrated_review": f"{scene_dir}/{directory}/07_scale_integrated_review_srgb_prores4444.mov",
                "review_sha256": sha256(review),
                "review_metadata": metadata,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

    social_source = cv2.imread(str(assets / "v45-t020-projection.jpg"))
    if social_source is None:
        raise RuntimeError("failed to read V45 projection still for social image")
    target_ratio = 1731 / 909
    crop_height = round(social_source.shape[1] / target_ratio)
    crop_y = (social_source.shape[0] - crop_height) // 2
    social_crop = social_source[crop_y : crop_y + crop_height]
    social = cv2.resize(social_crop, (1731, 909), interpolation=cv2.INTER_AREA)
    if not cv2.imwrite(str(site_root / "public" / "og-v45.png"), social):
        raise RuntimeError("failed to write V45 social image")

    manifest = {
        "release": "V45 official CIE 1931 2-degree 1 nm observer",
        "release_class": "measured_observer_revision",
        "only_image_change": "2383 analytical observer: official CIE table and 1 nm trapezoidal integration",
        "frozen": "V44/V42 5279, DIR, MTF, grain, scan, black, contrast, gamma and delivery",
        "dimensions": list(VIDEO_SIZE),
        "large_still_dimensions": [1920, 1440],
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "web_authority": "same middle frame decoded from each final encoded review movie",
        "timing": timings,
        "same_negative_ablation": public_value(
            json.loads((release / "v44_v45_same_negative_frame0.json").read_text())
        ),
        "native_release_audit": {
            "all_gates_pass": json.loads(
                (release / "v45_release_audit.json").read_text()
            )["all_gates_pass"],
            "branch_pass": {
                scene: {
                    branch: record["pass"]
                    for branch, record in branches.items()
                }
                for scene, branches in json.loads(
                    (release / "v45_release_audit.json").read_text()
                )["scenes"].items()
            },
        },
        "delivery_audit": {
            "pass": json.loads(
                (release / "v45_delivery_audit.json").read_text()
            )["pass"]
        },
        "verification": results,
    }
    (assets / "v45-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
