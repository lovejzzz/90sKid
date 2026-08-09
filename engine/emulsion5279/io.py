"""Native ProRes RAW input and colour-explicit ProRes output boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Iterator

import cv2
import numpy as np

from .contracts import DeliveryEncoding, RenderedFrame
from . import legacy


class ProResRawDecoder:
    """Stream AVFoundation's extended-linear BT.2020 float frames."""

    def __init__(
        self,
        executable: Path,
        source: Path,
        start_frame: int,
        frames: int,
    ) -> None:
        self.executable = Path(executable)
        self.source = Path(source)
        self.start_frame = int(start_frame)
        self.frames = int(frames)
        self.width, self.height, self.fps = legacy.model.probe_video(self.source)
        self._process: subprocess.Popen | None = None

    def __enter__(self) -> "ProResRawDecoder":
        self._process = subprocess.Popen(
            [
                str(self.executable),
                str(self.source),
                str(self.start_frame),
                str(self.frames),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return self

    def __iter__(self) -> Iterator[tuple[int, np.ndarray]]:
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("decoder must be used as a context manager")
        frame_bytes = self.width * self.height * 3 * 4
        for offset in range(self.frames):
            payload = self._process.stdout.read(frame_bytes)
            if len(payload) != frame_bytes:
                raise RuntimeError(
                    f"short ProRes RAW frame {offset}: {len(payload)} != {frame_bytes}"
                )
            frame = np.frombuffer(payload, dtype="<f4").reshape(
                self.height, self.width, 3
            )
            yield self.start_frame + offset, frame

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._process is None:
            return
        if self._process.stdout is not None:
            self._process.stdout.close()
        if exc_type is not None:
            self._process.terminate()
        status = self._process.wait()
        if exc_type is None and status != 0:
            raise RuntimeError(f"ProRes RAW decoder exited with status {status}")


def _xq_command(path: Path, width: int, height: int, fps: str) -> list[str]:
    command = legacy.model.prores_encoder_command(path, width, height, fps)
    command[command.index("-profile:v") + 1] = "5"
    return command


def _read_exact(stream, size: int) -> bytes:
    parts: list[bytes] = []
    remaining = size
    while remaining:
        part = stream.read(remaining)
        if not part:
            break
        parts.append(part)
        remaining -= len(part)
    return b"".join(parts)


def rebuild_srgb_companion_from_master(
    master: Path,
    companion: Path,
    frames: int,
) -> None:
    """Make the review movie and still from the delivered 12-bit master.

    This is the V39--V41 single-picture-authority contract.  The companion is
    not a second lossy realization from the pre-encode float image: it decodes
    the actual BT.1886 ProRes master, reconstructs reference light, and applies
    only the sRGB display transfer.
    """

    width, height, fps = legacy.model.probe_video(master)
    decoder = subprocess.Popen(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(master),
            "-map",
            "0:v:0",
            "-vf",
            (
                "setparams=color_primaries=bt709:color_trc=bt709:"
                "colorspace=bt709"
            ),
            "-frames:v",
            str(frames),
            "-pix_fmt",
            "rgb48le",
            "-f",
            "rawvideo",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    temporary = companion.with_name(companion.stem + ".rebuilt.mov")
    temporary.unlink(missing_ok=True)
    encoder = subprocess.Popen(
        _xq_command(temporary, width, height, fps), stdin=subprocess.PIPE
    )
    if decoder.stdout is None or encoder.stdin is None:
        raise RuntimeError("failed to open master-derived delivery pipes")
    frame_bytes = width * height * 3 * 2
    representative: np.ndarray | None = None
    completed = 0
    try:
        for frame_index in range(frames):
            payload = _read_exact(decoder.stdout, frame_bytes)
            if len(payload) != frame_bytes:
                break
            master_code = (
                np.frombuffer(payload, "<u2")
                .reshape(height, width, 3)
                .astype(np.float32)
                / 65535.0
            )
            light = legacy.model.bt1886_reference_decode(master_code)
            srgb = legacy.model.srgb_encode(light).astype(np.float32)
            encoded = np.rint(np.clip(srgb, 0.0, 1.0) * 65535.0).astype("<u2")
            encoder.stdin.write(encoded.tobytes())
            if frame_index == frames // 2:
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
            "master-derived sRGB rebuild failed: "
            f"decoder={decoder_status}, encoder={encoder_status}, "
            f"frames={completed}/{frames}"
        )
    legacy.model.finalize_prores_srgb_metadata(temporary)
    temporary.replace(companion)
    if representative is None:
        raise RuntimeError("no representative master-derived frame captured")
    pixels = np.rint(np.clip(representative, 0.0, 1.0) * 255.0).astype(np.uint8)
    cv2.imwrite(
        str(companion.parent / "still_emulsion.jpg"),
        cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR),
        [cv2.IMWRITE_JPEG_QUALITY, 96],
    )


def retain_source_audio_and_timecode(
    output: Path,
    source: Path,
    start_frame: int,
    frames: int,
    fps: str,
) -> dict[str, object]:
    """Apply the accepted V29 source-stream contract to every V42 movie."""

    from render_v29_full_release import (
        probe_source,
        remux_source_audio_and_timecode,
    )

    source_probe = probe_source(source)
    source_frames = int(source_probe["streams"][0]["nb_frames"])
    outputs: list[str] = []
    for directory in ("projection", "bluray_scan"):
        root = Path(output) / directory
        for filename, transfer in (
            ("05_emulsion_master_prores4444.mov", "rec709"),
            ("06_quicktime_preview_srgb_prores4444.mov", "srgb"),
        ):
            movie = root / filename
            remux_source_audio_and_timecode(
                movie,
                source,
                movie,
                "V42",
                start_frame=int(start_frame),
                frames=int(frames),
                fps=fps,
                source_frames=source_frames,
                transfer=transfer,
            )
            outputs.append(str(movie))
    return {
        "contract": "V29 frame-accurate source PCM/timecode retention",
        "source_frames": source_frames,
        "range": [int(start_frame), int(start_frame) + int(frames) - 1],
        "outputs_finalized": outputs,
    }


@dataclass(slots=True)
class _Writer:
    path: Path
    encoding: DeliveryEncoding
    process: subprocess.Popen

    @classmethod
    def open(
        cls,
        path: Path,
        encoding: DeliveryEncoding,
        width: int,
        height: int,
        fps: str,
    ) -> "_Writer":
        path.parent.mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(
            _xq_command(path, width, height, fps), stdin=subprocess.PIPE
        )
        return cls(path, encoding, process)

    def write(self, image: np.ndarray) -> None:
        if self.process.stdin is None:
            raise RuntimeError("encoder stdin is closed")
        encoded = np.rint(np.clip(image, 0.0, 1.0) * 65535.0).astype("<u2")
        self.process.stdin.write(encoded.tobytes())

    def close(self) -> None:
        if self.process.stdin is None:
            return
        self.process.stdin.close()
        if self.process.wait() != 0:
            raise RuntimeError(f"ProRes encoder failed: {self.path}")
        if self.encoding is DeliveryEncoding.REFERENCE_BT1886:
            legacy.model.finalize_prores_rec709_metadata(self.path)
        else:
            legacy.model.finalize_prores_srgb_metadata(self.path)


class DualDeliveryWriter:
    """Write two observer masters, then derive every viewing deliverable."""

    def __init__(
        self,
        output: Path,
        width: int,
        height: int,
        fps: str,
        frames: int,
    ) -> None:
        self.output = Path(output)
        self.frames = int(frames)
        self._writers: dict[tuple[str, DeliveryEncoding], _Writer] = {}
        for branch, directory in (
            ("projection", "projection"),
            ("scan", "bluray_scan"),
        ):
            root = self.output / directory
            self._writers[(branch, DeliveryEncoding.REFERENCE_BT1886)] = _Writer.open(
                root / "05_emulsion_master_prores4444.mov",
                DeliveryEncoding.REFERENCE_BT1886,
                width,
                height,
                fps,
            )

    def write(self, frame: RenderedFrame) -> None:
        encoded = frame.reference_master
        self._writers[("projection", encoded.encoding)].write(encoded.projection)
        self._writers[("scan", encoded.encoding)].write(encoded.scan)

    def close(self) -> None:
        errors: list[Exception] = []
        for writer in self._writers.values():
            try:
                writer.close()
            except Exception as error:  # close every stream before reporting
                errors.append(error)
        if errors:
            raise errors[0]
        for directory in ("projection", "bluray_scan"):
            root = self.output / directory
            rebuild_srgb_companion_from_master(
                root / "05_emulsion_master_prores4444.mov",
                root / "06_quicktime_preview_srgb_prores4444.mov",
                self.frames,
            )

    def __enter__(self) -> "DualDeliveryWriter":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if exc_type is None:
            self.close()
        else:
            for writer in self._writers.values():
                if writer.process.stdin is not None:
                    writer.process.stdin.close()
                writer.process.terminate()
                writer.process.wait()
