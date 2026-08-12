#!/usr/bin/env python3
"""Build V46 web media from the final encoded scale-integrated reviews."""

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
    release = site_root / "outputs" / "native_5k_v46_certified_spectral_inverse_1s"
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
            stem = f"v46-{scene_key}-{branch}"
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

    social_source = cv2.imread(str(assets / "v46-t020-projection.jpg"))
    if social_source is None:
        raise RuntimeError("failed to read V46 projection still for social image")
    target_ratio = 1731 / 909
    crop_height = round(social_source.shape[1] / target_ratio)
    crop_y = (social_source.shape[0] - crop_height) // 2
    social_crop = social_source[crop_y : crop_y + crop_height]
    social = cv2.resize(social_crop, (1731, 909), interpolation=cv2.INTER_AREA)
    if not cv2.imwrite(str(site_root / "public" / "og-v46.png"), social):
        raise RuntimeError("failed to write V46 social image")

    manifest = {
        "release": "V46 certified spectral inverse",
        "release_class": "stochastic_endpoint_and_nonnegative_inverse_correction",
        "image_changes": [
            "hold the complete stochastic state at published granularity endpoints",
            "replace clipped Status-M projection with exact active-set/KKT inverse",
        ],
        "evidence_boundary": "identity record formation; cross-record covariance remains unmeasured",
        "dimensions": list(VIDEO_SIZE),
        "large_still_dimensions": [1920, 1440],
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "web_authority": "same middle frame decoded from each final encoded review movie",
        "timing": timings,
        "spectral_precision": public_value(
            json.loads(
                (site_root / "engine" / "research_runs" / "v46_adaptive_real_frame_precision.json").read_text()
            )
        ),
        "pipeline_cache_coverage": public_value(
            json.loads(
                (site_root / "engine" / "research_runs" / "v46_pipeline_stage_cache_coverage_final.json").read_text()
            )
        ),
        "release_audits": {
            "paired_mean_relative_tail": public_value(
                json.loads(
                    (release / "v46_mean_relative_release_audit.json").read_text()
                )
            ),
            "master_companion_delivery": public_value(
                json.loads((release / "v46_delivery_audit.json").read_text())
            ),
            "final_decision": public_value(
                json.loads(
                    (release / "v46_final_release_decision.json").read_text()
                )
            ),
        },
        "verification": results,
    }
    (assets / "v46-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
