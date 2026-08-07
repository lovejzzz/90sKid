#!/usr/bin/env python3
"""Build V41 physical, FSD and deterministic web media from sRGB companions."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import cv2

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


def public_value(value: object) -> object:
    """Remove local absolute paths from the public provenance manifest."""
    if isinstance(value, dict):
        return {key: public_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_value(item) for item in value]
    if isinstance(value, str) and value.startswith("/"):
        return Path(value).name
    return value


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    release = site_root.parent / "outputs" / "native_5k_v41_chart_bounded_colour_1s"
    physical_root = release / "physical"
    comparator_root = release / "comparators"
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}
    timings: dict[str, object] = {}

    branch_sources = (
        ("projection", physical_root, "projection"),
        ("bluray", physical_root, "bluray_scan"),
        ("fsd", comparator_root, "fsd"),
        ("deterministic", comparator_root, "deterministic"),
    )
    for source in ("t002", "t007", "t031"):
        source_upper = source.upper()
        timings[source] = {
            "physical": public_value(json.loads(
                (physical_root / source_upper / "timing.json").read_text(encoding="utf-8")
            )),
            "comparators": public_value(json.loads(
                (comparator_root / source_upper / "timing.json").read_text(encoding="utf-8")
            )),
        }
        for branch, root, directory in branch_sources:
            companion = (
                root / source_upper / directory
                / "06_quicktime_preview_srgb_prores4444.mov"
            )
            if not companion.exists():
                raise FileNotFoundError(companion)
            stem = f"v41-{source}-{branch}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as temporary:
                metadata = decode_companion(companion, Path(temporary), large, small)
                encode_loop(Path(temporary), video)
            results[stem] = {
                "absolute_source_frames": FRAME_WINDOWS[source],
                "picture_authority": str(
                    root.relative_to(release) / source_upper / directory
                    / "05_emulsion_master_prores4444.mov"
                ),
                "source_companion": str(
                    root.relative_to(release) / source_upper / directory
                    / "06_quicktime_preview_srgb_prores4444.mov"
                ),
                "companion_metadata": metadata,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

    manifest = {
        "purpose": "V41 chart-bounded colour transport with controlled density comparisons",
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "absolute_source_frame_contract": FRAME_WINDOWS,
        "colour_evidence": {
            "fit": "T003 frame 160 DKC-Pro",
            "independent_holdout": "T005 frame 160 DKC-Pro, closer and mildly defocused",
            "strength": 0.125,
            "preserved": "D65 scene luminance and neutral axis",
            "withheld": "white balance, exposure, black, gamma and creative saturation",
        },
        "record_boundary": (
            "retain signed intermediate values only when all combined 5279 record "
            "exposures are non-negative; otherwise use the V40 non-negative basis"
        ),
        "pipelines": {
            "physical": "V40 stochastic 5279 formation with V41 shared colour input",
            "fsd": "N=176, sigma=0.597 px independent finite-site density control",
            "deterministic": "same mean colour and observer with stochastic density disabled",
        },
        "professional_master": "Rec.709 / inverse BT.1886 gamma 2.4 / 12-bit ProRes 4444 XQ",
        "quicktime_companion": "Rec.709 primaries / IEC sRGB transfer / 12-bit ProRes 4444 XQ",
        "web": "decoded only from the companion; hover frame zero and JPEG share source frame 12",
        "proxy_encoding": "H.264 High / yuv420p / CRF 18 / tune grain / closed GOP 6",
        "timing": timings,
        "verification": results,
    }
    (assets / "v41-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    chart_overlay = (
        site_root.parent / "research_runs" / "2026-08-07_t005_colorchecker"
        / "frame160_audit" / "patch_sampling_overlay.jpg"
    )
    chart = cv2.imread(str(chart_overlay), cv2.IMREAD_COLOR)
    if chart is None:
        raise FileNotFoundError(chart_overlay)
    if chart.shape[1] > 2560:
        height = round(chart.shape[0] * 2560 / chart.shape[1])
        chart = cv2.resize(chart, (2560, height), interpolation=cv2.INTER_AREA)
    research_assets = site_root / "public" / "research"
    research_assets.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(
        str(research_assets / "t005-dkc-pro-sampling.jpg"), chart,
        [cv2.IMWRITE_JPEG_QUALITY, 96],
    )


if __name__ == "__main__":
    main()
