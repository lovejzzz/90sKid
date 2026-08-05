#!/usr/bin/env python3
"""Build V35 sRGB still/live proxies from three native film trials."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_v25_web_previews import (
    FPS,
    FRAME_COUNT,
    REPRESENTATIVE_FRAME,
    VIDEO_SIZE,
    decode_master,
    verify,
)
from build_v34_web_previews import encode_loop


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    project_root = site_root.parent
    film_root = (
        project_root / "outputs" / "native_5k_v35_pipeline_bernoulli_u32_1s"
    )
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}

    for source in ("t002", "t007", "t031"):
        source_upper = source.upper()
        jobs = {
            "projection": (
                film_root / source_upper / "projection"
                / "05_emulsion_master_prores4444.mov",
                "projection",
            ),
            "bluray": (
                film_root / source_upper / "bluray_scan"
                / "05_emulsion_master_prores4444.mov",
                "bluray",
            ),
        }
        for branch_name, (master, branch_kind) in jobs.items():
            if not master.exists():
                raise FileNotFoundError(master)
            stem = f"v35-{source}-{branch_name}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as directory:
                probe = decode_master(
                    master,
                    branch_kind,
                    Path(directory),
                    large,
                    small,
                    0,
                )
                encode_loop(Path(directory), video)
            results[stem] = {
                "native_master": str(master),
                "master_metadata": probe,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

        camera_stem = f"v33-{source}-camera-as-shot"
        camera_video = assets / f"{camera_stem}-live-srgb.mp4"
        camera_still = assets / f"{camera_stem}.jpg"
        if not camera_video.exists() or not camera_still.exists():
            raise FileNotFoundError(f"missing frozen V33 camera witness: {camera_stem}")
        results[f"{source}-camera-reuse"] = {
            "source": camera_stem,
            **verify(camera_video, camera_still),
        }

    manifest = {
        "purpose": (
            "V35 quality-first Production graph with frozen V34 image model "
            "and frozen V33 0-stop As Shot camera witnesses"
        ),
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "film_pipeline": (
            "V34 photographic equations; V35 Philox-u32/Metal execution graph"
        ),
        "camera_pipeline": (
            "V33 Panasonic V-709 As Shot 0.00-stop witness; no film pipeline"
        ),
        "web": "Rec.709 light converted to sRGB IEC 61966-2-1",
        "proxy_encoding": (
            "H.264 High / yuv420p / CRF 22 / tune grain; native masters remain "
            "5760x4320 12-bit ProRes 4444"
        ),
        "verification": results,
    }
    (assets / "v35-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
