#!/usr/bin/env python3
"""Build V47 SHM web witnesses from the final encoded review movies."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import cv2

from build_v38_web_previews import encode_loop, verify
from build_v44_web_previews import decode_review, public_value, sha256


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    release = site_root / "outputs/native_5k_v47_shm_thicktail_1s/T020"
    assets = site_root / "public/versions"
    results: dict[str, object] = {}
    for branch, directory in (("projection", "shm_projection"), ("bluray", "shm_scan")):
        review = release / directory / "07_scale_integrated_review_srgb_prores4444.mov"
        stem = f"v47-t020-{branch}"
        large = assets / f"{stem}.jpg"
        small = assets / f"{stem}-sm.jpg"
        video = assets / f"{stem}-live-srgb.mp4"
        with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
            metadata = decode_review(review, Path(temporary), large, small)
            encode_loop(Path(temporary), video)
        results[stem] = {
            "native_master": f"{directory}/05_emulsion_master_prores4444.mov",
            "scale_integrated_review": f"{directory}/07_scale_integrated_review_srgb_prores4444.mov",
            "review_sha256": sha256(review),
            "review_metadata": metadata,
            **verify(video, large),
        }
        print(f"built {stem}", flush=True)

    social_source = cv2.imread(str(assets / "v47-t020-projection.jpg"))
    if social_source is None:
        raise RuntimeError("failed to read V47 projection still for social image")
    target_ratio = 1731 / 909
    crop_height = round(social_source.shape[1] / target_ratio)
    crop_y = (social_source.shape[0] - crop_height) // 2
    social = cv2.resize(
        social_source[crop_y : crop_y + crop_height],
        (1731, 909),
        interpolation=cv2.INTER_AREA,
    )
    if not cv2.imwrite(str(site_root / "public/og-v47.png"), social):
        raise RuntimeError("failed to write V47 social image")

    manifest = {
        "release": "V47 Silver-Halide Morphology comparator",
        "release_class": "controlled_silver_efex_same_class_morphology",
        "frames": 24,
        "dimensions": [1920, 1440],
        "source_frames": [0, 23],
        "web_authority": "same middle frame decoded from each final encoded review movie",
        "formation_boundary": (
            "SHM replaces only the independent post-observer finite-density comparator; "
            "it is not represented as measured 5279 three-record morphology"
        ),
        "morphology_audit": public_value(
            json.loads(
                (site_root / "engine/research_runs/v47_shm_morphology_audit.json").read_text()
            )
        ),
        "temporal_audit": public_value(
            json.loads(
                (site_root / "engine/research_runs/v47_shm_temporal_audit.json").read_text()
            )
        ),
        "delivery_audit": public_value(
            json.loads(
                (site_root / "engine/research_runs/v47_shm_delivery_audit.json").read_text()
            )
        ),
        "verification": results,
    }
    (assets / "v47-shm-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
