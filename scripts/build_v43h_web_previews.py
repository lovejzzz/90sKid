#!/usr/bin/env python3
"""Build V43H four-view web media from delivered sRGB companions."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_v38_web_previews import (
    FRAME_COUNT,
    FPS,
    REPRESENTATIVE_FRAME,
    VIDEO_SIZE,
    decode_companion,
    encode_loop,
    verify,
)


FRAME_WINDOWS = {
    "t020": [0, 23],
    "t032": [0, 23],
    "t007": [276, 299],
}
BRANCHES = (
    ("projection", "projection", "05_emulsion_master_prores4444.mov"),
    ("bluray", "bluray_scan", "05_emulsion_master_prores4444.mov"),
    ("fsd", "fsd", "05_emulsion_master_prores4444.mov"),
    ("camera", "camera_baseline", "05_camera_baseline_prores4444.mov"),
)


def public_value(value: object) -> object:
    """Strip local absolute paths from public provenance."""
    if isinstance(value, dict):
        return {key: public_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_value(item) for item in value]
    if isinstance(value, str) and value.startswith("/"):
        return Path(value).name
    return value


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    release = site_root / "outputs" / "native_5k_v43h_hypothesis_1s"
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}
    timings: dict[str, object] = {}

    for source in FRAME_WINDOWS:
        source_upper = source.upper()
        scene_root = release / source_upper
        timings[source] = public_value(
            json.loads((scene_root / "timing.json").read_text(encoding="utf-8"))
        )
        for branch, directory, master_name in BRANCHES:
            branch_root = scene_root / directory
            companion = branch_root / "06_quicktime_preview_srgb_prores4444.mov"
            manifest = json.loads(
                (branch_root / "manifest.json").read_text(encoding="utf-8")
            )
            if not companion.exists():
                raise FileNotFoundError(companion)
            stem = f"v43h-{source}-{branch}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
                metadata = decode_companion(companion, Path(temporary), large, small)
                encode_loop(Path(temporary), video)
            results[stem] = {
                "absolute_source_frames": FRAME_WINDOWS[source],
                "picture_authority": f"{source_upper}/{directory}/{master_name}",
                "source_companion": (
                    f"{source_upper}/{directory}/"
                    "06_quicktime_preview_srgb_prores4444.mov"
                ),
                "master_sha256": manifest["master_sha256"],
                "companion_sha256": manifest["companion_sha256"],
                "release_class": manifest["release_class"],
                "companion_metadata": metadata,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

    manifest = {
        "release": "V43H Hypothesis Edition",
        "release_class": "hypothesis_not_measurement",
        "question": (
            "If the most likely but still unmeasured parts of the existing "
            "5279 research are completed with bounded central estimates, what "
            "might the stock look like?"
        ),
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "absolute_source_frame_contract": FRAME_WINDOWS,
        "pipelines": {
            "projection": "V43H 5279 negative → 2383 xenon projection observer",
            "scan": "same V43H negative → bounded period Spirit/Cineon observer",
            "fsd": "independent post-observer finite-site density control",
            "camera": "Apple Standard ProRes RAW → Panasonic official V-709; no film pipeline",
        },
        "professional_master": (
            "Rec.709 / BT.1886 gamma 2.4 / 12-bit ProRes 4444 XQ"
        ),
        "quicktime_companion": (
            "Rec.709 primaries / IEC sRGB transfer / 12-bit ProRes 4444 XQ"
        ),
        "web": (
            "decoded only from each encoded sRGB companion; hover frame zero "
            "and JPEG share source frame 12"
        ),
        "proxy_encoding": (
            "H.264 High / yuv420p / CRF 18 / tune grain / closed GOP 6"
        ),
        "timing": timings,
        "verification": results,
    }
    (assets / "v43h-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
