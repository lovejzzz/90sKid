#!/usr/bin/env python3
"""Build matched-frame V36 sRGB still/live proxies."""

from __future__ import annotations

import json
import subprocess
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


FRAME_WINDOWS = {"t002": [0, 23], "t007": [276, 299], "t031": [132, 155]}


def encode_loop(frame_dir: Path, output: Path) -> None:
    """Use a short GOP so motion prediction cannot turn grain into long bursts."""
    encoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{VIDEO_SIZE[0]}x{VIDEO_SIZE[1]}",
            "-r", FPS, "-i", "pipe:0", "-an",
            "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-tune", "grain",
            "-crf", "18", "-g", "6", "-keyint_min", "6", "-sc_threshold", "0",
            "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
            "-color_trc", "iec61966-2-1", "-colorspace", "bt709",
            "-bsf:v", (
                "h264_metadata=colour_primaries=1:transfer_characteristics=13:"
                "matrix_coefficients=1:video_full_range_flag=0"
            ),
            "-movflags", "+faststart", str(output),
        ],
        stdin=subprocess.PIPE,
    )
    assert encoder.stdin is not None
    order = list(range(REPRESENTATIVE_FRAME, FRAME_COUNT)) + list(
        range(REPRESENTATIVE_FRAME)
    )
    for index in order:
        encoder.stdin.write((frame_dir / f"{index:02d}.rgb").read_bytes())
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError(f"failed to encode {output}")


def main() -> None:
    site_root = Path(__file__).resolve().parents[1]
    project_root = site_root.parent
    roots = {
        # T002 already used the correct frame-zero window in V35; V36 has no
        # image-model change, so preserve its validated native masters.
        "t002": project_root / "outputs" / "native_5k_v35_pipeline_bernoulli_u32_1s",
        "t007": project_root / "outputs" / "native_5k_v36_matched_35mm_1s",
        "t031": project_root / "outputs" / "native_5k_v36_matched_35mm_1s",
    }
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}

    for source in ("t002", "t007", "t031"):
        source_upper = source.upper()
        jobs = {
            "projection": (
                roots[source] / source_upper / "projection"
                / "05_emulsion_master_prores4444.mov",
                "projection",
            ),
            "bluray": (
                roots[source] / source_upper / "bluray_scan"
                / "05_emulsion_master_prores4444.mov",
                "bluray",
            ),
        }
        for branch_name, (master, branch_kind) in jobs.items():
            if not master.exists():
                raise FileNotFoundError(master)
            stem = f"v36-{source}-{branch_name}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as directory:
                probe = decode_master(
                    master, branch_kind, Path(directory), large, small, 0
                )
                encode_loop(Path(directory), video)
            results[stem] = {
                "absolute_source_frames": FRAME_WINDOWS[source],
                "native_master": str(master),
                "master_metadata": probe,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)

        camera_stem = f"v33-{source}-camera-as-shot"
        camera_video = assets / f"{camera_stem}-live-srgb.mp4"
        camera_still = assets / f"{camera_stem}.jpg"
        if not camera_video.exists() or not camera_still.exists():
            raise FileNotFoundError(f"missing frozen camera witness: {camera_stem}")
        results[f"{source}-camera-reuse"] = {
            "source": camera_stem,
            "absolute_source_frames": FRAME_WINDOWS[source],
            **verify(camera_video, camera_still),
        }

    manifest = {
        "purpose": "V36 matched-frame 35 mm image-structure release",
        "dimensions": list(VIDEO_SIZE),
        "fps": FPS,
        "frames": FRAME_COUNT,
        "representative_frame": REPRESENTATIVE_FRAME,
        "absolute_source_frame_contract": FRAME_WINDOWS,
        "film_pipeline": "V35 image model and Production graph; no retune",
        "camera_pipeline": "V33 Panasonic V-709 As Shot witness; no film pipeline",
        "web": "Rec.709 light converted to sRGB IEC 61966-2-1",
        "proxy_encoding": (
            "H.264 High / yuv420p / CRF 18 / tune grain / closed 6-frame GOP; "
            "native masters remain 5760x4320 12-bit ProRes 4444"
        ),
        "verification": results,
    }
    (assets / "v36-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
