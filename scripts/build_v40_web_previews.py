#!/usr/bin/env python3
"""Build V40 web media only from the delivered master-derived sRGB copies."""

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
    root = site_root.parent / "outputs" / "native_5k_v40_colour_grain_repair_1s"
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
        for branch_name, directory in (("projection", "projection"), ("bluray", "bluray_scan")):
            companion = root / source_upper / directory / "06_quicktime_preview_srgb_prores4444.mov"
            stem = f"v40-{source}-{branch_name}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
                metadata = decode_companion(companion, Path(temporary), large, small)
                encode_loop(Path(temporary), video)
            results[stem] = {
                "absolute_source_frames": FRAME_WINDOWS[source],
                "picture_authority": f"{source_upper}/{directory}/05_emulsion_master_prores4444.mov",
                "source_companion": f"{source_upper}/{directory}/06_quicktime_preview_srgb_prores4444.mov",
                "companion_metadata": metadata,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

    manifest = {
        "purpose": "V40 colour-grain covariance repair release",
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "absolute_source_frame_contract": FRAME_WINDOWS,
        "v39_status": "withdrawn: unvalidated cross-record high-frequency tails",
        "film_pipeline": (
            "formed 5279 density plus published post-process residual; "
            "deterministic 2383 density/MTF; no unmeasured stochastic print-grain term"
        ),
        "colour_grain_boundary": (
            "observer-side opponent integration restored; the final V31 adapter does "
            "not re-add its high-frequency opponent residual; isolated 3x3 dark "
            "primary impulses are release-gated on every frame"
        ),
        "raw_record_boundary": (
            "signed intermediate film-basis cancellation withdrawn; physical record "
            "formation uses bounded non-negative film RGB"
        ),
        "artistic_grade": "none; accepted V38 colour, black and gamma remain frozen",
        "professional_master": "Rec.709 / inverse BT.1886 gamma 2.4 / 12-bit ProRes 4444 XQ",
        "quicktime_companion": (
            "derived from the encoded master / Rec.709 primaries / IEC sRGB transfer / "
            "12-bit ProRes 4444 XQ"
        ),
        "web": (
            "decoded only from the master-derived companion; hover frame zero and JPEG "
            "share source frame 12"
        ),
        "proxy_encoding": "H.264 High / yuv420p / CRF 15 / tune grain / closed GOP 6",
        "timing": timings,
        "verification": results,
    }
    (assets / "v40-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
