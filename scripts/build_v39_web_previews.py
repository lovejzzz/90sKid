#!/usr/bin/env python3
"""Build V39 still/live media from the exact sRGB QuickTime companions."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_v38_web_previews import (
    FRAME_COUNT,
    FRAME_WINDOWS,
    FPS,
    REPRESENTATIVE_FRAME,
    VIDEO_SIZE,
    decode_companion,
    encode_loop,
    verify,
)


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    root = (
        site_root.parent
        / "outputs"
        / "native_5k_v39_density_reconstruction_1s"
    )
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}
    timings: dict[str, object] = {}

    for source in ("t002", "t007", "t031"):
        source_upper = source.upper()
        timing_path = root / source_upper / "timing.json"
        timing = json.loads(timing_path.read_text(encoding="utf-8"))
        command = timing.get("pipeline_provenance", {}).get("command", [])
        timing.get("pipeline_provenance", {})["command"] = [
            Path(value).name if isinstance(value, str) and value.startswith("/") else value
            for value in command
        ]
        timings[source] = timing
        for branch_name, directory in (
            ("projection", "projection"),
            ("bluray", "bluray_scan"),
        ):
            companion = (
                root
                / source_upper
                / directory
                / "06_quicktime_preview_srgb_prores4444.mov"
            )
            stem = f"v39-{source}-{branch_name}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
                metadata = decode_companion(
                    companion, Path(temporary), large, small
                )
                encode_loop(Path(temporary), video)
            results[stem] = {
                "absolute_source_frames": FRAME_WINDOWS[source],
                "source_companion": (
                    f"{source_upper}/{directory}/"
                    "06_quicktime_preview_srgb_prores4444.mov"
                ),
                "companion_metadata": metadata,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

    manifest = {
        "purpose": "V39 density-formation reconstruction release",
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "absolute_source_frame_contract": FRAME_WINDOWS,
        "film_pipeline": (
            "processed 5279 density MTF + pre-DIR dye-yield calibration; "
            "2383 MTF and finite dye clouds in Status-A density"
        ),
        "raw_record_boundary": (
            "preserve signed film-basis components through the record matrix; "
            "clamp physical exposure once after record formation"
        ),
        "artistic_grade": "none; V38 colour, black and gamma frozen",
        "professional_master": (
            "Rec.709 / inverse BT.1886 gamma 2.4 / 12-bit ProRes 4444"
        ),
        "quicktime_companion": (
            "master-derived Rec.709 primaries / IEC sRGB transfer / "
            "12-bit ProRes 4444 XQ"
        ),
        "web": (
            "decoded directly from the sRGB companion; hover frame zero is "
            "the same source frame as the static JPEG"
        ),
        "proxy_encoding": (
            "H.264 High / yuv420p / CRF 15 / tune grain / closed GOP 6"
        ),
        "timing": timings,
        "verification": results,
    }
    (assets / "v39-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
