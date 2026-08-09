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
    """Write both observers in reference-master and QuickTime encodings."""

    def __init__(self, output: Path, width: int, height: int, fps: str) -> None:
        self.output = Path(output)
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
            self._writers[(branch, DeliveryEncoding.QUICKTIME_SRGB)] = _Writer.open(
                root / "06_quicktime_preview_srgb_prores4444.mov",
                DeliveryEncoding.QUICKTIME_SRGB,
                width,
                height,
                fps,
            )

    def write(self, frame: RenderedFrame) -> None:
        for encoded in (frame.reference_master, frame.quicktime_companion):
            self._writers[("projection", encoded.encoding)].write(encoded.projection)
            self._writers[("scan", encoded.encoding)].write(encoded.scan)

    def save_stills(self, frame: RenderedFrame) -> None:
        for branch, image in (
            ("projection", frame.quicktime_companion.projection),
            ("bluray_scan", frame.quicktime_companion.scan),
        ):
            output = self.output / branch / "still_emulsion.jpg"
            pixels = np.rint(np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8)
            cv2.imwrite(
                str(output),
                cv2.cvtColor(pixels, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, 96],
            )

    def close(self) -> None:
        errors: list[Exception] = []
        for writer in self._writers.values():
            try:
                writer.close()
            except Exception as error:  # close every stream before reporting
                errors.append(error)
        if errors:
            raise errors[0]

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
