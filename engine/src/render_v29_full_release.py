#!/usr/bin/env python3
"""Render a profile-locked source in exact parallel ranges and preserve sound."""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v29_profile
import v30_profile
import v34_profile
import v36_profile
import v37_profile
import v38_profile
import v39_profile
from render_v23_dual_masters import save_srgb_still, save_still, sha256


def probe_source(path: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=nb_frames,width,height,avg_frame_rate:format=duration",
            "-of", "json", str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def split_ranges(start: int, frames: int, workers: int) -> list[tuple[int, int]]:
    worker_count = max(1, min(workers, frames))
    base, remainder = divmod(frames, worker_count)
    ranges: list[tuple[int, int]] = []
    cursor = start
    for index in range(worker_count):
        count = base + (1 if index < remainder else 0)
        ranges.append((cursor, count))
        cursor += count
    return ranges


def memory_safe_worker_count(requested: int, frames: int) -> tuple[int, dict[str, object]]:
    """Keep native 5.7K float workers away from macOS swap exhaustion."""
    physical_bytes = int(subprocess.check_output(
        ["sysctl", "-n", "hw.memsize"], text=True
    ).strip())
    gib = 1024**3
    # Native profiling on this M4 Max measured 9.1 GiB peak RSS for V30.  Keep
    # a 13 GiB planning envelope for V34's integrated colour boundary and a
    # 26 GiB host/app reserve. A two-worker 48 GiB probe was byte-identical but
    # consumed 6.6 GiB of swap, so parallel native workers require >=64 GiB and
    # healthy launch-time memory pressure. Three workers are never allowed.
    reserve_bytes = 26 * gib
    estimated_worker_bytes = 13 * gib
    safe_limit = min(
        2,
        max(1, (physical_bytes - reserve_bytes) // estimated_worker_bytes),
    )
    if physical_bytes < 64 * gib:
        safe_limit = 1
    pressure_free_percent: int | None = None
    try:
        pressure = subprocess.check_output(
            ["memory_pressure", "-Q"], text=True, stderr=subprocess.DEVNULL
        )
        match = re.search(r"free percentage:\s*(\d+)%", pressure)
        if match:
            pressure_free_percent = int(match.group(1))
            if pressure_free_percent < 60:
                safe_limit = 1
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    selected_request = requested if requested > 0 else safe_limit
    selected = max(1, min(selected_request, safe_limit, frames))
    return selected, {
        "physical_memory_gib": physical_bytes / gib,
        "reserved_for_os_and_apps_gib": reserve_bytes / gib,
        "estimated_peak_per_native_worker_gib": estimated_worker_bytes / gib,
        "requested_workers": requested if requested > 0 else "auto",
        "safe_worker_limit": safe_limit,
        "selected_workers": selected,
        "memory_pressure_free_percent_at_launch": pressure_free_percent,
        "high_pressure_single_worker_threshold_percent": 60,
        "minimum_practical_memory_for_two_workers_gib": 64,
        "policy": "quality-invariant scheduling cap; no image kernel changes",
    }


def concat_escape(path: Path) -> str:
    return str(path.resolve()).replace("'", "'\\''")


def concat_video(parts: list[Path], destination: Path, work: Path) -> None:
    listing = work / f"{destination.parent.name}_concat.txt"
    listing.write_text(
        "".join(f"file '{concat_escape(part)}'\n" for part in parts),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
            "-i", str(listing), "-map", "0:v:0", "-c", "copy", str(destination),
        ],
        check=True,
    )


def remux_source_audio_and_timecode(
    video_only: Path,
    source: Path,
    destination: Path,
    version_label: str,
    *,
    start_frame: int,
    frames: int,
    fps: str,
    source_frames: int,
    transfer: str = "rec709",
) -> None:
    """Attach source sound and timecode with frame-accurate range semantics.

    Complete-source renders retain the original PCM and timecode tracks by
    stream copy.  Selected ranges decode/re-encode only the lossless PCM audio
    so ``atrim`` can begin and end on the exact requested sample; their timecode
    track is regenerated at the corresponding source-frame address.
    """
    temporary = destination.with_name(destination.stem + ".muxing.mov")
    if transfer == "rec709":
        frame_transfer = "bt709"
        container_transfer = "bt709"
    elif transfer == "srgb":
        frame_transfer = "unknown"
        container_transfer = "iec61966-2-1"
    else:
        raise ValueError(f"unsupported delivery transfer: {transfer}")
    common = [
        "-bsf:v",
        (
            "prores_metadata=color_primaries=bt709:"
            f"color_trc={frame_transfer}:colorspace=bt709"
        ),
        "-color_primaries", "bt709", "-color_trc", container_transfer,
        "-colorspace", "bt709",
        "-movflags", "write_colr", "-map_metadata", "1",
        "-metadata:s:v:0", f"encoder=5279 Emulsion Project {version_label}",
    ]
    if start_frame == 0 and frames == source_frames:
        command = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(video_only), "-i", str(source),
            "-map", "0:v:0", "-map", "1:a?", "-map", "1:d?",
            "-c", "copy", *common, str(temporary),
        ]
    else:
        rate = Fraction(fps)
        start_seconds = float(Fraction(start_frame, 1) / rate)
        duration_seconds = float(Fraction(frames, 1) / rate)
        source_timecode = probe_timecode(source)
        range_timecode = offset_timecode(source_timecode, start_frame, rate)
        command = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(video_only), "-i", str(source),
            "-filter_complex",
            (
                f"[1:a:0]atrim=start={start_seconds:.12f}:"
                f"duration={duration_seconds:.12f},asetpts=PTS-STARTPTS[a]"
            ),
            "-map", "0:v:0", "-map", "[a]",
            "-c:v", "copy", "-c:a", "pcm_s24le",
            "-timecode", range_timecode,
            *common, str(temporary),
        ]
    subprocess.run(command, check=True)
    temporary.replace(destination)


def probe_timecode(path: Path) -> str:
    payload = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "d:0",
            "-show_entries", "stream_tags=timecode", "-of", "json", str(path),
        ],
        text=True,
    )
    streams = json.loads(payload).get("streams", [])
    if not streams:
        return "00:00:00:00"
    return streams[0].get("tags", {}).get("timecode", "00:00:00:00")


def offset_timecode(timecode: str, frame_offset: int, rate: Fraction) -> str:
    """Offset the colon-delimited, non-drop GH7 source timecode."""
    separator = ";" if ";" in timecode else ":"
    if separator == ";":
        raise ValueError("drop-frame partial-range timecode is not yet supported")
    hours, minutes, seconds, frames = (int(value) for value in timecode.split(":"))
    nominal_fps = round(float(rate))
    total = (((hours * 60 + minutes) * 60 + seconds) * nominal_fps + frames)
    total += frame_offset
    frames = total % nominal_fps
    total //= nominal_fps
    seconds = total % 60
    total //= 60
    minutes = total % 60
    hours = (total // 60) % 24
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{frames:02d}"


def extract_representative(
    master: Path,
    frame: int,
    width: int,
    height: int,
    transfer: str = "bt709",
) -> np.ndarray:
    payload = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(master),
            "-vf",
            (
                f"select=eq(n\\,{frame}),"
                "setparams=color_primaries=bt709:"
                f"color_trc={transfer}:colorspace=bt709"
            ),
            "-frames:v", "1",
            "-pix_fmt", "rgb48le", "-f", "rawvideo", "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return np.frombuffer(payload, dtype="<u2").reshape(height, width, 3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=0, help="0 means all remaining frames")
    parser.add_argument(
        "--workers", type=int, default=0,
        help="0 selects a memory-safe count; explicit values are capped safely",
    )
    parser.add_argument("--worker-threads", type=int, default=8)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument("--grain-scale", type=float, default=1.0)
    parser.add_argument(
        "--no-source-audio",
        action="store_true",
        help="keep a selected validation range video-only",
    )
    parser.add_argument(
        "--renderer",
        choices=("v29", "v30", "v34", "v36", "v37", "v38", "v39"),
        default="v29",
        help="profile-locked segment renderer; default preserves V29 behavior",
    )
    args = parser.parse_args()

    profile_module = {
        "v29": v29_profile,
        "v30": v30_profile,
        "v34": v34_profile,
        "v36": v36_profile,
        "v37": v37_profile,
        "v38": v38_profile,
        "v39": v39_profile,
    }[args.renderer]
    renderer_script = Path(__file__).with_name(
        {
            "v29": "render_v29_dual_masters.py",
            "v30": "render_v30_dual_masters.py",
            "v34": "render_v34_dual_masters.py",
            "v36": "render_v36_dual_masters.py",
            "v37": "render_v37_dual_masters.py",
            "v38": "render_v38_dual_masters.py",
            "v39": "render_v39_dual_masters.py",
        }[args.renderer]
    )
    version_label = profile_module.PROFILE["short_name"]

    source_info = probe_source(args.input)
    video_info = source_info["streams"][0]
    source_frames = int(video_info["nb_frames"])
    frames = args.frames or (source_frames - args.start_frame)
    if frames < 1 or args.start_frame < 0 or args.start_frame + frames > source_frames:
        raise ValueError("requested frame range is outside the source")
    width = int(video_info["width"])
    height = int(video_info["height"])
    fps = str(video_info["avg_frame_rate"])
    worker_count, memory_policy = memory_safe_worker_count(args.workers, frames)
    ranges = split_ranges(args.start_frame, frames, worker_count)
    args.output.mkdir(parents=True, exist_ok=True)
    wall_started = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="v29-full-") as temporary_name:
        temporary_root = Path(temporary_name)
        processes: list[tuple[subprocess.Popen[bytes], object, Path, int, int]] = []
        for index, (segment_start, segment_frames) in enumerate(ranges):
            segment_output = temporary_root / f"segment_{index:02d}"
            log_handle = (args.output / f"segment_{index:02d}.log").open("wb")
            command = [
                sys.executable,
                str(renderer_script),
                str(args.input), str(segment_output),
                "--decoder", str(args.decoder),
                "--start-frame", str(segment_start),
                "--frames", str(segment_frames),
                "--exposure-stops", str(args.exposure_stops),
                "--grain-scale", str(args.grain_scale),
                "--oversample", "1",
                "--opencv-threads", str(args.worker_threads),
                "--binomial-workers", str(args.worker_threads),
                "--numba-threads", str(args.worker_threads),
                "--array-workers", str(args.worker_threads),
                "--accelerated-cpu-exact",
            ]
            if args.renderer in ("v36", "v37", "v38", "v39"):
                command.append("--v35-production-pipeline")
            process = subprocess.Popen(command, stdout=log_handle, stderr=subprocess.STDOUT)
            processes.append((process, log_handle, segment_output, segment_start, segment_frames))

        segment_reports: list[dict[str, object]] = []
        for process, log_handle, segment_output, segment_start, segment_frames in processes:
            return_code = process.wait()
            log_handle.close()
            if return_code != 0:
                log_path = args.output / f"segment_{ranges.index((segment_start, segment_frames)):02d}.log"
                raise RuntimeError(
                    f"{version_label} segment failed; inspect {log_path}"
                )
            timing = json.loads((segment_output / "timing.json").read_text())
            segment_reports.append(
                {
                    "start_frame": segment_start,
                    "frames": segment_frames,
                    "wall_seconds": timing["total_wall_seconds_before_hashes"],
                    "effective_seconds_per_frame_for_two_masters": timing[
                        "effective_seconds_per_frame_for_two_masters"
                    ],
                    "stage_summaries": timing["stage_summaries"],
                }
            )

        final_paths: dict[str, Path] = {}
        quicktime_paths: dict[str, Path] = {}
        delivery_files = [
            ("reference", "05_emulsion_master_prores4444.mov", "rec709")
        ]
        if args.renderer in ("v38", "v39"):
            delivery_files.append(
                (
                    "quicktime",
                    "06_quicktime_preview_srgb_prores4444.mov",
                    "srgb",
                )
            )
        for observer, directory_name in (
            ("projection", "projection"), ("scan", "bluray_scan")
        ):
            output_dir = args.output / directory_name
            output_dir.mkdir(parents=True, exist_ok=True)
            for delivery_name, filename, transfer in delivery_files:
                final_path = output_dir / filename
                video_only = temporary_root / f"{observer}_{delivery_name}_video_only.mov"
                parts = [
                    temporary_root / f"segment_{index:02d}" / directory_name /
                    filename
                    for index in range(len(ranges))
                ]
                concat_video(parts, video_only, temporary_root)
                if args.no_source_audio:
                    shutil.copy2(video_only, final_path)
                else:
                    remux_source_audio_and_timecode(
                        video_only,
                        args.input,
                        final_path,
                        version_label,
                        start_frame=args.start_frame,
                        frames=frames,
                        fps=fps,
                        source_frames=source_frames,
                        transfer=transfer,
                    )
                if delivery_name == "reference":
                    final_paths[observer] = final_path
                else:
                    quicktime_paths[observer] = final_path

        representative_frame = frames // 2
        for observer, directory_name in (("projection", "projection"), ("scan", "bluray_scan")):
            if args.renderer in ("v38", "v39"):
                image = extract_representative(
                    quicktime_paths[observer],
                    representative_frame,
                    width,
                    height,
                    transfer="iec61966-2-1",
                ).astype(np.float32) / 65535.0
                save_srgb_still(
                    args.output / directory_name / "still_emulsion.jpg", image
                )
            else:
                image = extract_representative(
                    final_paths[observer], representative_frame, width, height
                ).astype(np.float32) / 65535.0
                save_still(
                    args.output / directory_name / "still_emulsion.jpg",
                    image,
                    observer,
                )

    wall_seconds = time.perf_counter() - wall_started
    source_duration = float(source_info["format"]["duration"])
    timing = {
        "clock": "time.perf_counter monotonic wall clock",
        "architecture": "memory-capped exact CPU frame ranges; stream-copy concat; source PCM/timecode remux",
        "workers": len(ranges),
        "worker_threads": args.worker_threads,
        "memory_policy": memory_policy,
        "segments": segment_reports,
        "total_wall_seconds_before_final_hashes": wall_seconds,
        "effective_wall_seconds_per_source_frame_for_two_masters": wall_seconds / frames,
    }
    (args.output / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")
    common = {
        "release": profile_module.PROFILE["name"],
        "profile": args.renderer,
        "input": str(args.input),
        "input_sha256": sha256(args.input),
        "input_dimensions": [width, height],
        "source_frames": source_frames,
        "start_frame": args.start_frame,
        "frames_processed": frames,
        "fps": fps,
        "source_duration_seconds": source_duration,
        "negative_constraint": profile_module.PROFILE["negative_constraint"],
        "negative_change": profile_module.PROFILE.get("negative_change"),
        "pipeline_change": profile_module.PROFILE.get("pipeline_change"),
        "grain_temporal_contract": profile_module.PROFILE.get(
            "grain_temporal_contract"
        ),
        "grain_subpixel_phase_mode": profile_module.PROFILE.get(
            "grain_subpixel_phase_mode"
        ),
        "grain_subpixel_phase_radius_native_px": profile_module.PROFILE.get(
            "grain_subpixel_phase_radius_native_px"
        ),
        "grain_stable_phase_offset_degrees": profile_module.PROFILE.get(
            "grain_stable_phase_offset_degrees"
        ),
        "final_projection_adapter": profile_module.PROFILE.get(
            "final_projection_adapter"
        ),
        "unidentified_parameter_policy": profile_module.PROFILE[
            "unidentified_parameter_policy"
        ],
        "temporal_contract": profile_module.PROFILE["temporal_contract"],
        "delivery_contract": profile_module.PROFILE["delivery_contract"],
        "shared_emulsion_realization_between_observers": True,
        "absolute_frame_seed_across_segments": True,
        "source_audio_and_timecode_retained": not args.no_source_audio,
        "timing": timing,
    }
    if args.no_source_audio:
        audio_description = "none (validation range requested video-only)"
    elif args.start_frame == 0 and frames == source_frames:
        audio_description = "source PCM s24le, 48 kHz, 4 channels, stream copied"
    else:
        audio_description = (
            "source PCM decoded, frame-accurately trimmed and losslessly "
            "re-encoded as PCM s24le; partial-range timecode regenerated"
        )
    for observer, directory_name, look in (
        ("projection", "projection", "2383_projection_monitor"),
        ("scan", "bluray_scan", "cineon_bluray"),
    ):
        master = final_paths[observer]
        manifest = {
            **common,
            "viewing_look": look,
            "output_encoding": (
                profile_module.PROFILE["reference_master_encoding"]
                if args.renderer in ("v38", "v39")
                else "12-bit ProRes 4444; Rec.709 1-1-1"
            ),
            "audio": audio_description,
            "master_sha256": sha256(master),
            "quicktime_companion": (
                str(quicktime_paths[observer])
                if args.renderer in ("v38", "v39") else None
            ),
            "quicktime_companion_encoding": (
                profile_module.PROFILE["quicktime_companion_encoding"]
                if args.renderer in ("v38", "v39") else None
            ),
            "quicktime_companion_sha256": (
                sha256(quicktime_paths[observer])
                if args.renderer in ("v38", "v39") else None
            ),
        }
        (args.output / directory_name / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(timing, indent=2), flush=True)


if __name__ == "__main__":
    main()
