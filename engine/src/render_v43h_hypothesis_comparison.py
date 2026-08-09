#!/usr/bin/env python3
"""Render V43H projection, period scan, FSD and camera witness together."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from engine.emulsion5279 import legacy
from engine.emulsion5279.contracts import EngineConfig, EngineMode
from engine.emulsion5279.io import (
    ProResRawDecoder,
    _read_exact,
    rebuild_srgb_companion_from_master,
)
from engine.emulsion5279.pipeline import Emulsion5279Engine

from fsd_density import apply_fsd
from render_v30_camera_baseline import (
    DEFAULT_V709_LUT,
    EXPECTED_V709_SHA256,
    V709_LEGAL_BLACK,
    V709_LEGAL_WHITE,
    load_cube,
)
from render_v23_dual_masters import sha256


FRAME_WINDOWS = {
    "T020": (0, 24),
    "T032": (0, 24),
    "T007": (276, 24),
}


def _xq_command(path: Path, width: int, height: int, fps: str) -> list[str]:
    command = legacy.model.prores_encoder_command(path, width, height, fps)
    command[command.index("-profile:v") + 1] = "5"
    return command


class MasterWriter:
    def __init__(self, path: Path, width: int, height: int, fps: str) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen(
            _xq_command(path, width, height, fps), stdin=subprocess.PIPE
        )

    def write(self, encoded: np.ndarray) -> None:
        if self.process.stdin is None:
            raise RuntimeError("master encoder is closed")
        payload = np.rint(np.clip(encoded, 0.0, 1.0) * 65535.0).astype("<u2")
        self.process.stdin.write(payload.tobytes())

    def close(self) -> None:
        if self.process.stdin is None:
            return
        self.process.stdin.close()
        if self.process.wait() != 0:
            raise RuntimeError(f"master encoder failed: {self.path}")
        legacy.model.finalize_prores_rec709_metadata(self.path)

    def abort(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        self.process.terminate()
        self.process.wait()


def rebuild_camera_srgb_companion_from_master(
    master: Path, companion: Path, frames: int
) -> None:
    """Derive the camera witness from its encoded Panasonic V-709 master."""
    e = legacy.model
    width, height, fps = e.probe_video(master)
    decoder = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(master),
            "-map", "0:v:0", "-frames:v", str(frames),
            "-vf", "setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709",
            "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    temporary = companion.with_name(companion.stem + ".rebuilt.mov")
    temporary.unlink(missing_ok=True)
    encoder = subprocess.Popen(
        _xq_command(temporary, width, height, fps), stdin=subprocess.PIPE
    )
    if decoder.stdout is None or encoder.stdin is None:
        raise RuntimeError("camera companion pipes did not open")
    frame_bytes = width * height * 3 * 2
    representative: np.ndarray | None = None
    completed = 0
    try:
        for offset in range(frames):
            payload = _read_exact(decoder.stdout, frame_bytes)
            if len(payload) != frame_bytes:
                break
            v709 = (
                np.frombuffer(payload, "<u2")
                .reshape(height, width, 3)
                .astype(np.float32)
                / 65535.0
            )
            srgb = e.srgb_encode(e.bt709_decode(v709)).astype(np.float32)
            encoder.stdin.write(
                np.rint(np.clip(srgb, 0.0, 1.0) * 65535.0)
                .astype("<u2")
                .tobytes()
            )
            if offset == frames // 2:
                representative = srgb.copy()
            completed += 1
    finally:
        decoder.stdout.close()
        encoder.stdin.close()
    decoder_status = decoder.wait()
    encoder_status = encoder.wait()
    if decoder_status or encoder_status or completed != frames:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            "camera master-derived companion failed: "
            f"decoder={decoder_status}, encoder={encoder_status}, "
            f"frames={completed}/{frames}"
        )
    e.finalize_prores_srgb_metadata(temporary)
    temporary.replace(companion)
    if representative is None:
        raise RuntimeError("camera representative frame was not captured")
    cv2.imwrite(
        str(companion.parent / "still_camera_baseline.jpg"),
        cv2.cvtColor(
            np.rint(np.clip(representative, 0.0, 1.0) * 255.0).astype(np.uint8),
            cv2.COLOR_RGB2BGR,
        ),
        [cv2.IMWRITE_JPEG_QUALITY, 96],
    )


def _summarize(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "total_seconds": float(array.sum()),
        "mean_seconds_per_frame": float(array.mean()),
        "p95_seconds_per_frame": float(np.percentile(array, 95)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int)
    parser.add_argument("--frames", type=int)
    parser.add_argument("--source-label", required=True, choices=tuple(FRAME_WINDOWS))
    parser.add_argument("--site-count", type=int, default=176)
    parser.add_argument("--correlation-sigma", type=float, default=0.597)
    parser.add_argument("--density-strength", type=float, default=1.0)
    args = parser.parse_args()

    default_start, default_frames = FRAME_WINDOWS[args.source_label]
    start_frame = default_start if args.start_frame is None else args.start_frame
    frames = default_frames if args.frames is None else args.frames
    if frames < 1:
        raise ValueError("frames must be positive")

    config = EngineConfig(profile="v43h", mode=EngineMode.PRODUCTION_METAL)
    engine = Emulsion5279Engine(config)
    engine.configure()
    e = legacy.model
    lut = load_cube(DEFAULT_V709_LUT)
    args.output.mkdir(parents=True, exist_ok=True)

    directories = {
        "projection": args.output / "projection",
        "bluray_scan": args.output / "bluray_scan",
        "fsd": args.output / "fsd",
        "camera": args.output / "camera_baseline",
    }
    master_names = {
        "projection": "05_emulsion_master_prores4444.mov",
        "bluray_scan": "05_emulsion_master_prores4444.mov",
        "fsd": "05_emulsion_master_prores4444.mov",
        "camera": "05_camera_baseline_prores4444.mov",
    }

    timings: dict[str, list[float]] = {
        "decode_read": [],
        "negative_formation": [],
        "physical_dual_observer": [],
        "deterministic_observer": [],
        "fsd_density": [],
        "camera_witness": [],
        "encode_write_four": [],
    }
    fsd_stats: list[dict[str, float | int | str]] = []
    started = time.perf_counter()
    writers: dict[str, MasterWriter] = {}
    width = height = 0
    fps = ""
    try:
        with ProResRawDecoder(
            args.decoder, args.input, start_frame, frames
        ) as decoder:
            width, height, fps = decoder.width, decoder.height, decoder.fps
            writers = {
                name: MasterWriter(
                    directory / master_names[name], width, height, fps
                )
                for name, directory in directories.items()
            }
            frame_iterator = iter(decoder)
            for offset in range(frames):
                mark = time.perf_counter()
                try:
                    absolute_frame, raw = next(frame_iterator)
                except StopIteration as exc:
                    raise RuntimeError(
                        f"RAW decoder ended after {offset}/{frames} frames"
                    ) from exc
                timings["decode_read"].append(time.perf_counter() - mark)

                mark = time.perf_counter()
                negative = engine.form_negative(raw, absolute_frame)
                timings["negative_formation"].append(time.perf_counter() - mark)

                mark = time.perf_counter()
                observers, deterministic_observers = engine.observe_with_mean(
                    negative, absolute_frame
                )
                reference = engine.encode_reference(observers)
                timings["physical_dual_observer"].append(time.perf_counter() - mark)

                mark = time.perf_counter()
                deterministic = deterministic_observers.projection_linear_rec709
                timings["deterministic_observer"].append(time.perf_counter() - mark)

                mark = time.perf_counter()
                fsd, stats = apply_fsd(
                    deterministic,
                    absolute_frame,
                    site_count=args.site_count,
                    correlation_sigma=args.correlation_sigma,
                    density_strength=args.density_strength,
                )
                stats["absolute_frame"] = absolute_frame
                fsd_stats.append(stats)
                fsd_master = e.bt1886_reference_encode(fsd).astype(np.float32)
                timings["fsd_density"].append(time.perf_counter() - mark)

                mark = time.perf_counter()
                vgamut = e.bt2020_to_panasonic_vgamut(raw)
                vlog = e.vlog_encode(vgamut)
                legal_v709 = e.apply_rgb_cube_lut(vlog, lut)
                camera = np.clip(
                    (legal_v709 - V709_LEGAL_BLACK)
                    / (V709_LEGAL_WHITE - V709_LEGAL_BLACK),
                    0.0,
                    1.0,
                ).astype(np.float32)
                timings["camera_witness"].append(time.perf_counter() - mark)

                mark = time.perf_counter()
                writers["projection"].write(reference.projection)
                writers["bluray_scan"].write(reference.scan)
                writers["fsd"].write(fsd_master)
                writers["camera"].write(camera)
                timings["encode_write_four"].append(time.perf_counter() - mark)

                elapsed = time.perf_counter() - started
                eta = elapsed / (offset + 1) * (frames - offset - 1)
                print(
                    f"V43H {args.source_label} frame {offset + 1}/{frames} · "
                    f"elapsed {elapsed:.1f}s · ETA {eta:.1f}s",
                    flush=True,
                )
                del raw, negative, observers, deterministic_observers, reference
                del deterministic, fsd, fsd_master
                del vgamut, vlog, legal_v709, camera
        for writer in writers.values():
            writer.close()
    except Exception:
        for writer in writers.values():
            writer.abort()
        raise

    sampler = engine.validate_rendered_frames(frames)
    finalization_started = time.perf_counter()
    for branch in ("projection", "bluray_scan", "fsd"):
        root = directories[branch]
        rebuild_srgb_companion_from_master(
            root / master_names[branch],
            root / "06_quicktime_preview_srgb_prores4444.mov",
            frames,
        )
    rebuild_camera_srgb_companion_from_master(
        directories["camera"] / master_names["camera"],
        directories["camera"] / "06_quicktime_preview_srgb_prores4444.mov",
        frames,
    )

    from render_v29_full_release import probe_source, remux_source_audio_and_timecode

    source_frames = int(probe_source(args.input)["streams"][0]["nb_frames"])
    for branch, root in directories.items():
        for filename, transfer in (
            (master_names[branch], "rec709"),
            ("06_quicktime_preview_srgb_prores4444.mov", "srgb"),
        ):
            movie = root / filename
            remux_source_audio_and_timecode(
                movie,
                args.input,
                movie,
                "V43H Hypothesis Edition",
                start_frame=start_frame,
                frames=frames,
                fps=fps,
                source_frames=source_frames,
                transfer=transfer,
            )
    finalization_seconds = time.perf_counter() - finalization_started

    common = {
        "release": "V43H Hypothesis Edition",
        "release_class": "hypothesis_not_measurement",
        "question": engine.profile.PROFILE["question"],
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "source_label": args.source_label,
        "start_frame": start_frame,
        "frames": frames,
        "dimensions": [width, height],
        "fps": fps,
        "engine": engine.provenance,
        "hypotheses": {
            "negative_nps": engine.profile.PROFILE["negative_nps_hypothesis"],
            "spirit": engine.profile.PROFILE["spirit_hypothesis"],
            "2383_print_grain": engine.profile.PROFILE["print_grain_hypothesis"],
        },
        "frozen": engine.profile.PROFILE["frozen"],
        "withheld": engine.profile.PROFILE["explicitly_withheld"],
        "fsd_contract": {
            "site_count": args.site_count,
            "correlation_sigma_native_px": args.correlation_sigma,
            "density_strength": args.density_strength,
            "domain": "post-observer IEC 61966-2-1 signal",
            "independent_pipeline": True,
        },
        "camera_contract": {
            "decode": "Apple Standard ProRes RAW extended-linear BT.2020/D65",
            "display": "Panasonic official V-Log to V-709 LUT",
            "exposure_stops": 0.0,
            "film_pipeline": "none",
            "v709_lut_sha256": EXPECTED_V709_SHA256,
        },
        "sampler_audit": sampler,
    }
    for branch, root in directories.items():
        manifest = {
            **common,
            "branch": branch,
            "master": master_names[branch],
            "master_sha256": sha256(root / master_names[branch]),
            "companion": "06_quicktime_preview_srgb_prores4444.mov",
            "companion_sha256": sha256(
                root / "06_quicktime_preview_srgb_prores4444.mov"
            ),
        }
        if branch == "fsd":
            manifest["fsd_frame_stats"] = fsd_stats
        (root / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    report = {
        "release": "V43H Hypothesis Edition",
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "input": str(args.input),
        "source_label": args.source_label,
        "range": [start_frame, start_frame + frames - 1],
        "stage_summaries": {
            name: _summarize(values) for name, values in timings.items()
        },
        "finalization_seconds": finalization_seconds,
        "total_wall_seconds": time.perf_counter() - started,
        "effective_seconds_per_frame": (
            (time.perf_counter() - started) / frames
        ),
        "command": [sys.executable, *sys.argv],
    }
    (args.output / "timing.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
