#!/usr/bin/env python3
"""Validate and consolidate the three-scene V34 native release."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import v34_profile
from render_v23_dual_masters import sha256


SCENES = {
    "T002": {
        "source": "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV",
        "start_frame": 0,
    },
    "T007": {
        "source": "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T007.MOV",
        "start_frame": 276,
    },
    "T031": {
        "source": "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T031.MOV",
        "start_frame": 132,
    },
}


def probe(path: Path) -> dict[str, object]:
    payload = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_streams", "-show_format",
            "-of", "json", str(path),
        ],
        text=True,
    )
    report = json.loads(payload)
    video = next(stream for stream in report["streams"] if stream["codec_type"] == "video")
    audio = next(
        (stream for stream in report["streams"] if stream["codec_type"] == "audio"),
        None,
    )
    data = next(
        (stream for stream in report["streams"] if stream["codec_type"] == "data"),
        None,
    )
    result: dict[str, object] = {
        "width": int(video["width"]),
        "height": int(video["height"]),
        "frames": int(video["nb_frames"]),
        "pix_fmt": video["pix_fmt"],
        "bits_per_raw_sample": int(video["bits_per_raw_sample"]),
        "color_range": video.get("color_range"),
        "color_space": video.get("color_space"),
        "color_transfer": video.get("color_transfer"),
        "color_primaries": video.get("color_primaries"),
    }
    if audio:
        result["audio"] = {
            "codec": audio["codec_name"],
            "sample_fmt": audio.get("sample_fmt"),
            "sample_rate": int(audio["sample_rate"]),
            "channels": int(audio["channels"]),
            "duration_ts": int(audio.get("duration_ts", 0)),
        }
    if data:
        result["timecode"] = data.get("tags", {}).get("timecode")
    return result


def assert_delivery(report: dict[str, object], path: Path) -> None:
    expected = {
        "width": 5760,
        "height": 4320,
        "frames": 24,
        "pix_fmt": "yuv444p12le",
        "bits_per_raw_sample": 12,
        "color_space": "bt709",
        "color_transfer": "bt709",
        "color_primaries": "bt709",
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise RuntimeError(f"{path}: {key}={report.get(key)!r}; expected {value!r}")
    audio = report.get("audio")
    if not isinstance(audio, dict):
        raise RuntimeError(f"{path}: missing partial-range source audio")
    if (audio.get("codec"), audio.get("sample_rate"), audio.get("channels")) != (
        "pcm_s24le", 48000, 4
    ):
        raise RuntimeError(f"{path}: unexpected audio {audio}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "outputs" / "native_5k_v34_processed_mtf_1s"
    release: dict[str, object] = {
        "release": v34_profile.PROFILE["name"],
        "profile": v34_profile.PROFILE,
        "native_raster": [5760, 4320],
        "frames_per_scene": 24,
        "output": "12-bit ProRes 4444 · Rec.709 1-1-1",
        "creative_grade": "none",
        "scenes": {},
    }
    total_wall = 0.0
    for scene, description in SCENES.items():
        timing_path = output / scene / "timing.json"
        timing = json.loads(timing_path.read_text(encoding="utf-8"))
        total_wall += float(timing["total_wall_seconds_before_final_hashes"])
        scene_result = {
            **description,
            "frames": 24,
            "timing": timing,
            "branches": {},
        }
        for branch, directory in (
            ("projection", "projection"),
            ("bluray_scan", "bluray_scan"),
        ):
            master = output / scene / directory / "05_emulsion_master_prores4444.mov"
            delivery = probe(master)
            assert_delivery(delivery, master)
            manifest_path = output / scene / directory / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "release": v34_profile.PROFILE["name"],
                    "profile": "v34",
                    "negative_constraint": v34_profile.PROFILE["negative_constraint"],
                    "negative_change": v34_profile.PROFILE["negative_change"],
                    "pipeline_change": v34_profile.PROFILE["pipeline_change"],
                    "final_projection_adapter": v34_profile.PROFILE[
                        "final_projection_adapter"
                    ],
                    "audio": (
                        "source PCM decoded, frame-accurately trimmed and "
                        "losslessly re-encoded as PCM s24le; partial-range "
                        "timecode regenerated"
                    ),
                    "master_sha256": sha256(master),
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            scene_result["branches"][branch] = {
                "path": str(master),
                "sha256": sha256(master),
                "delivery": delivery,
            }
        release["scenes"][scene] = scene_result
    release["total_sequential_wall_seconds"] = total_wall
    (output / "release_manifest.json").write_text(
        json.dumps(release, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"validated_scenes": list(SCENES), "wall_seconds": total_wall}, indent=2))


if __name__ == "__main__":
    main()
