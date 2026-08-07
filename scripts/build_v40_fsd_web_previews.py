#!/usr/bin/env python3
"""Build the V40 FSD and deterministic-control web media.

The published physical-V40 assets remain authoritative and are not rebuilt.
Every new JPEG and H.264 loop is derived from the 12-bit sRGB viewing
companion, with frame 12 shared by the still and first hover-video frame.
"""

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
    root = site_root.parent / "outputs" / "native_5k_v40_fsd_comparator_1s"
    physical_root = site_root.parent / "outputs" / "native_5k_v40_colour_grain_repair_1s"
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}

    for source in ("t002", "t007", "t031"):
        source_upper = source.upper()
        for branch in ("fsd", "deterministic"):
            companion = (
                root / source_upper / branch
                / "06_quicktime_preview_srgb_prores4444.mov"
            )
            if not companion.exists():
                raise FileNotFoundError(companion)
            stem = f"v40-{source}-{branch}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
                metadata = decode_companion(companion, Path(temporary), large, small)
                encode_loop(Path(temporary), video)
            results[stem] = {
                "absolute_source_frames": FRAME_WINDOWS[source],
                "picture_authority": f"{source_upper}/{branch}/05_emulsion_master_prores4444.mov",
                "source_companion": f"{source_upper}/{branch}/06_quicktime_preview_srgb_prores4444.mov",
                "companion_metadata": metadata,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

    manifest = {
        "purpose": "V40 physical 5279 / FSD / deterministic controlled comparison",
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "absolute_source_frame_contract": FRAME_WINDOWS,
        "physical_v40": {
            "status": "unchanged canonical V40 release",
            "root": physical_root.name,
        },
        "fsd": {
            "name": "Finite-Site Density",
            "site_count": 176,
            "inverse_binomial_lookup": [512, 512],
            "correlation_sigma_native_pixels": 0.597,
            "strength": 1.0,
            "density_domain": "post-observer IEC 61966-2-1 signal",
            "colour_rule": "fixed deterministic opponent field; gamut-limit the density excursion only; no independent RGB impulses",
            "status": "independent comparator, not a replacement for physical 5279",
        },
        "deterministic": (
            "same RAW, colour, black, gamma, 5279 expectation and 2383 observer; "
            "stochastic density disabled"
        ),
        "professional_master": "Rec.709 / inverse BT.1886 gamma 2.4 / 12-bit ProRes 4444 XQ",
        "quicktime_companion": "Rec.709 primaries / IEC sRGB transfer / 12-bit ProRes 4444 XQ",
        "web": "decoded only from the companion; hover frame zero and JPEG share source frame 12",
        "proxy_encoding": "H.264 High / yuv420p / CRF 18 / tune grain / closed GOP 6",
        "verification": results,
    }
    (assets / "v40-fsd-comparator-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
