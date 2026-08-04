#!/usr/bin/env python3
"""Consolidate and verify all nine matched V30 web previews."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from build_v25_web_previews import verify


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    assets = site_root / "public" / "versions"
    masters = site_root.parent / "outputs" / "native_5k_v30_1s"
    results: dict[str, object] = {}
    for source in ("t002", "t020", "t032"):
        source_dir = masters / source.upper()
        branches = {
            "projection": source_dir / "projection" / "05_emulsion_master_prores4444.mov",
            "bluray": source_dir / "bluray_scan" / "05_emulsion_master_prores4444.mov",
            "camera": source_dir / "camera_baseline" / "05_camera_baseline_prores4444.mov",
        }
        for branch, master in branches.items():
            stem = f"v30-{source}-{branch}"
            probe = json.loads(subprocess.check_output(
                [
                    "ffprobe", "-v", "error", "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,nb_frames,pix_fmt,bits_per_raw_sample,color_space,color_transfer,color_primaries",
                    "-of", "json", str(master),
                ], text=True,
            ))["streams"][0]
            results[stem] = {
                "master_metadata": probe,
                **verify(assets / f"{stem}-live-srgb.mp4", assets / f"{stem}.jpg"),
            }
    manifest = {
        "purpose": "V30 matched Rec.709-to-sRGB web proxies from three 12-bit camera/film result sets",
        "dimensions": [1920, 1440],
        "fps": "24000/1001",
        "frames": 24,
        "source_frame_range": [0, 23],
        "first_frame_source_index": 12,
        "projection_source": "Rec.709-D65 1-1-1 monitor rendering of the 48-nit gamma-2.6 cinema observer",
        "bluray_source": "Rec.709-D65 1-1-1 Blu-ray rendering; BT.1886 is the reference display EOTF",
        "camera_source": "Panasonic official V-Log to V-709 display transform only; no 5279, 2383, scan or creative grade",
        "web": "sRGB IEC 61966-2-1; no browser-dependent master interpretation",
        "proxy_encoding": "H.264 High / yuv420p / CRF 20 / tune grain; archive masters remain 5.7K 12-bit ProRes 4444",
        "verification": results,
    }
    (assets / "v30-live-preview-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
