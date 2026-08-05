#!/usr/bin/env python3
"""Build V33 0-stop as-shot web witnesses for three frozen film trials."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_v25_web_previews import decode_master, encode_loop, verify


SCENES = ("t002", "t007", "t031")


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    release = site_root.parent / "outputs/native_5k_v33_boundary_1s"
    assets = site_root / "public/versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}
    for source in SCENES:
        stem = f"v33-{source}-camera-as-shot"
        master = (
            release / source.upper() / "camera_as_shot_0stop"
            / "05_camera_baseline_prores4444.mov"
        )
        large = assets / f"{stem}.jpg"
        small = assets / f"{stem}-sm.jpg"
        video = assets / f"{stem}-live-srgb.mp4"
        with tempfile.TemporaryDirectory(prefix=f"{stem}-") as directory:
            probe = decode_master(
                master, "camera", Path(directory), large, small, start_frame=0
            )
            encode_loop(Path(directory), video)
        results[stem] = {"master_metadata": probe, **verify(video, large)}
        print(f"built {stem}", flush=True)
    manifest = {
        "purpose": (
            "V33 0-stop as-shot Panasonic V-709 exposure witnesses; frozen "
            "projection/scan media reuse the accepted V31/V32 web assets"
        ),
        "dimensions": [1920, 1440],
        "fps": "24000/1001",
        "frames": 24,
        "representative_frame": 12,
        "camera_exposure_stops": 0.0,
        "film_virtual_exposure_stops": 0.45,
        "technical_neutral_enabled": False,
        "web": "Rec.709 OETF decoded to light, then sRGB IEC 61966-2-1",
        "verification": results,
    }
    (assets / "v33-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
