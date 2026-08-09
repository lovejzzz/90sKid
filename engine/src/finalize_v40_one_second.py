#!/usr/bin/env python3
"""Build V40's viewing copy from the encoded master and retain source A/V metadata."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from finalize_v39_one_second import rebuild_srgb_companion_from_delivered_master
from render_v23_dual_masters import sha256
from render_v29_full_release import probe_source, remux_source_audio_and_timecode

PRINT_LUT_CACHE = "cache/print_2383_monitor_output_lut_193_v30.npy"
PRINT_LUT_SHA256 = (
    "5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c"
)
PRINT_OBSERVER_EXECUTION = (
    "hybrid: analytical observer for the deterministic spatial 2383 density "
    "mean; validated pointwise negative-density output LUT for the signed "
    "5279 stochastic observer delta"
)


def correct_v40_print_observer_provenance(record: dict) -> None:
    """Correct a V40 reporting-only predicate; rendered pixels are unchanged."""
    for key, value in tuple(record.items()):
        if key == "print_lut_sha256":
            record[key] = PRINT_LUT_SHA256
        elif key == "print_observer_execution":
            record[key] = PRINT_OBSERVER_EXECUTION
        elif key == "validated_print_lut_cache":
            record[key] = PRINT_LUT_CACHE
        elif key == "validated_print_lut_sha256":
            record[key] = PRINT_LUT_SHA256
        elif isinstance(value, dict):
            correct_v40_print_observer_provenance(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start-frame", type=int, required=True)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--release-id", default="V40")
    args = parser.parse_args()

    source_probe = probe_source(args.source)
    stream = source_probe["streams"][0]
    source_frames = int(stream["nb_frames"])
    fps = str(stream["avg_frame_rate"])
    started = time.perf_counter()

    for directory_name in ("projection", "bluray_scan"):
        directory = args.output / directory_name
        master = directory / "05_emulsion_master_prores4444.mov"
        companion = directory / "06_quicktime_preview_srgb_prores4444.mov"

        # There is one picture authority: the encoded 12-bit BT.1886 master.
        # Rebuild the Mac/sRGB copy from that file instead of independently
        # realizing a second lossy ProRes picture.
        rebuild_srgb_companion_from_delivered_master(master, companion, args.frames)
        for movie, transfer in ((master, "rec709"), (companion, "srgb")):
            remux_source_audio_and_timecode(
                movie,
                args.source,
                movie,
                args.release_id,
                start_frame=args.start_frame,
                frames=args.frames,
                fps=fps,
                source_frames=source_frames,
                transfer=transfer,
            )

        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        correct_v40_print_observer_provenance(manifest)
        manifest.update(
            {
                "source_audio_and_timecode_retained": True,
                "audio": (
                    "source PCM decoded, frame-accurately trimmed and losslessly "
                    "re-encoded as PCM s24le; partial-range timecode regenerated"
                ),
                "picture_authority": (
                    "encoded 12-bit BT.1886 professional master; every viewing "
                    "deliverable and website asset is derived from this authority"
                ),
                "quicktime_companion_authority": (
                    "decoded delivered BT.1886 professional master; sRGB OETF; "
                    "12-bit ProRes 4444 XQ"
                ),
                "master_sha256": sha256(master),
                "quicktime_companion_sha256": sha256(companion),
            }
        )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    elapsed = time.perf_counter() - started
    timing_path = args.output / "timing.json"
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    correct_v40_print_observer_provenance(timing)
    timing["audio_timecode_and_authority_finalize_seconds"] = elapsed
    render_seconds = float(
        timing.get("total_wall_seconds_before_hashes", timing.get("total_seconds", 0.0))
    )
    timing["total_with_audio_timecode_seconds"] = render_seconds + elapsed
    timing_path.write_text(json.dumps(timing, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(timing, indent=2))


if __name__ == "__main__":
    main()
