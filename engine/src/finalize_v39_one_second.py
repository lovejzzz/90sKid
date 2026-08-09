#!/usr/bin/env python3
"""Attach source audio/timecode and refresh V39 one-second provenance."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

import emulsion_experiment as e
from render_v23_dual_masters import save_srgb_still
from render_v23_dual_masters import sha256
from render_v29_full_release import probe_source, remux_source_audio_and_timecode


def read_exact(stream, size: int) -> bytes:
    parts: list[bytes] = []
    remaining = size
    while remaining:
        part = stream.read(remaining)
        if not part:
            break
        parts.append(part)
        remaining -= len(part)
    return b"".join(parts)


def rebuild_srgb_companion_from_delivered_master(
    master: Path,
    companion: Path,
    frames: int,
) -> None:
    """Derive the Mac viewing copy from the actual encoded BT.1886 master.

    V38 encoded BT.1886 and sRGB copies independently from floating-point
    observer light.  That was adequate for smooth scan imagery, but the finer
    V39 projection-density structure made the two independent lossy ProRes
    realizations measurably diverge.  Decode the delivered master once, recover
    its reference light, and only then encode sRGB so both deliverables share
    the same 12-bit picture authority.
    """

    width, height, fps = e.probe_video(master)
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(master), "-map", "0:v:0",
            "-vf", "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
            "-frames:v", str(frames), "-pix_fmt", "rgb48le",
            "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    temporary = companion.with_name(companion.stem + ".rebuilt.mov")
    encoder_command = e.prores_encoder_command(temporary, width, height, fps)
    encoder_command[encoder_command.index("-profile:v") + 1] = "5"
    encoder = subprocess.Popen(
        encoder_command,
        stdin=subprocess.PIPE,
    )
    assert decoder.stdout is not None and encoder.stdin is not None
    frame_bytes = width * height * 3 * 2
    representative: np.ndarray | None = None
    completed = 0
    try:
        for frame_index in range(frames):
            payload = read_exact(decoder.stdout, frame_bytes)
            if len(payload) != frame_bytes:
                break
            master_code = (
                np.frombuffer(payload, "<u2")
                .reshape(height, width, 3)
                .astype(np.float32)
                / 65535.0
            )
            master_light = e.bt1886_reference_decode(master_code)
            srgb = e.srgb_encode(master_light).astype(np.float32)
            encoded = np.rint(srgb * 65535.0).astype("<u2")
            encoder.stdin.write(encoded.tobytes())
            if frame_index == frames // 2:
                representative = srgb.copy()
            completed += 1
    finally:
        decoder.stdout.close()
        encoder.stdin.close()
    decoder_rc = decoder.wait()
    encoder_rc = encoder.wait()
    if decoder_rc or encoder_rc or completed != frames:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            "master-derived sRGB rebuild failed: "
            f"decoder={decoder_rc}, encoder={encoder_rc}, frames={completed}/{frames}"
        )
    e.finalize_prores_srgb_metadata(temporary)
    temporary.replace(companion)
    if representative is None:
        raise RuntimeError("no representative frame captured")
    save_srgb_still(companion.parent / "still_emulsion.jpg", representative)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start-frame", type=int, required=True)
    parser.add_argument("--frames", type=int, default=24)
    args = parser.parse_args()

    source_probe = probe_source(args.source)
    stream = source_probe["streams"][0]
    source_frames = int(stream["nb_frames"])
    fps = str(stream["avg_frame_rate"])
    started = time.perf_counter()

    for directory_name in ("projection", "bluray_scan"):
        directory = args.output / directory_name
        files = (
            (directory / "05_emulsion_master_prores4444.mov", "rec709"),
            (directory / "06_quicktime_preview_srgb_prores4444.mov", "srgb"),
        )
        rebuild_srgb_companion_from_delivered_master(
            files[0][0], files[1][0], args.frames
        )
        for movie, transfer in files:
            remux_source_audio_and_timecode(
                movie,
                args.source,
                movie,
                "V39",
                start_frame=args.start_frame,
                frames=args.frames,
                fps=fps,
                source_frames=source_frames,
                transfer=transfer,
            )

        manifest_path = directory / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update(
            {
                "source_audio_and_timecode_retained": True,
                "audio": (
                    "source PCM decoded, frame-accurately trimmed and losslessly "
                    "re-encoded as PCM s24le; partial-range timecode regenerated"
                ),
                "quicktime_companion_authority": (
                    "decoded delivered BT.1886 professional master; sRGB OETF; "
                    "12-bit ProRes 4444 XQ"
                ),
                "master_sha256": sha256(files[0][0]),
                "quicktime_companion_sha256": sha256(files[1][0]),
            }
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    elapsed = time.perf_counter() - started
    timing_path = args.output / "timing.json"
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    timing["audio_timecode_finalize_seconds"] = elapsed
    render_seconds = float(
        timing.get(
            "total_wall_seconds_before_hashes",
            timing.get("total_seconds", 0.0),
        )
    )
    timing["total_with_audio_timecode_seconds"] = render_seconds + elapsed
    timing_path.write_text(json.dumps(timing, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(timing, indent=2))


if __name__ == "__main__":
    main()
