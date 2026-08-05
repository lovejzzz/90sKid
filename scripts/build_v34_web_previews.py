#!/usr/bin/env python3
"""Build V34 sRGB still/live proxies from three native film trials."""

from __future__ import annotations

import json
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


def encode_loop(frame_dir: Path, output: Path) -> None:
    """Encode a compact hover proxy; archive masters and stills stay untouched."""
    import subprocess

    encoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
            "-pix_fmt", "rgb24", "-s", f"{VIDEO_SIZE[0]}x{VIDEO_SIZE[1]}",
            "-r", FPS, "-i", "pipe:0", "-an",
            "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-tune", "grain",
            "-crf", "22", "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709", "-color_trc", "iec61966-2-1",
            "-colorspace", "bt709",
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
    film_root = project_root / "outputs" / "native_5k_v34_processed_mtf_1s"
    assets = site_root / "public" / "versions"
    assets.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}

    for source in ("t002", "t007", "t031"):
        source_upper = source.upper()
        jobs = {
            "projection": (
                film_root / source_upper / "projection"
                / "05_emulsion_master_prores4444.mov",
                "projection",
            ),
            "bluray": (
                film_root / source_upper / "bluray_scan"
                / "05_emulsion_master_prores4444.mov",
                "bluray",
            ),
        }
        for branch_name, (master, branch_kind) in jobs.items():
            if not master.exists():
                raise FileNotFoundError(master)
            stem = f"v34-{source}-{branch_name}"
            large = assets / f"{stem}.jpg"
            small = assets / f"{stem}-sm.jpg"
            video = assets / f"{stem}-live-srgb.mp4"
            with tempfile.TemporaryDirectory(prefix=f"{stem}-web-") as directory:
                probe = decode_master(
                    master,
                    branch_kind,
                    Path(directory),
                    large,
                    small,
                    0,
                )
                encode_loop(Path(directory), video)
            results[stem] = {
                "native_master": str(master),
                "master_metadata": probe,
                **verify(video, large),
            }
            print(f"built {stem}", flush=True)
        camera_stem = f"v33-{source}-camera-as-shot"
        camera_video = assets / f"{camera_stem}-live-srgb.mp4"
        camera_still = assets / f"{camera_stem}.jpg"
        if not camera_video.exists() or not camera_still.exists():
            raise FileNotFoundError(f"missing frozen V33 camera witness: {camera_stem}")
        results[f"{source}-camera-reuse"] = {
            "source": camera_stem,
            **verify(camera_video, camera_still),
        }

    manifest = {
        "purpose": (
            "V34 processed-MTF/single-generation film results with frozen "
            "V33 0-stop As Shot camera witnesses"
        ),
        "dimensions": [1920, 1440],
        "fps": "24000/1001",
        "frames": 24,
        "representative_frame": 12,
        "film_pipeline": (
            "V34 one-generation 12-bit Rec.709 projection and period-scan masters"
        ),
        "camera_pipeline": (
            "V33 Panasonic V-709 As Shot 0.00-stop witness; no film pipeline"
        ),
        "web": "Rec.709 light converted to sRGB IEC 61966-2-1",
        "proxy_encoding": (
            "H.264 High / yuv420p / CRF 22 / tune grain; native masters remain "
            "5760x4320 12-bit ProRes 4444"
        ),
        "verification": results,
    }
    (assets / "v34-live-preview-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
