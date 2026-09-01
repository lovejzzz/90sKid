"""FFmpeg-backed video probing, decoding and encoding."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np


def ffmpeg_binary() -> str:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # pragma: no cover - fallback path
        path = shutil.which("ffmpeg")
        if path is None:
            raise RuntimeError("ffmpeg not found; install imageio-ffmpeg or a system ffmpeg")
        return path


def ffprobe_binary() -> str | None:
    return shutil.which("ffprobe")


def probe(path: str | Path) -> dict:
    """Return width, height, fps, frame count, duration, colour tags and audio flag."""
    path = str(path)
    probe_bin = ffprobe_binary()
    info: dict = {"path": path}
    if probe_bin is not None:
        result = subprocess.run(
            [probe_bin, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
            if video is None:
                raise RuntimeError("no video stream found")
            info.update(_stream_info(video, data.get("format", {})))
            info["has_audio"] = any(s.get("codec_type") == "audio" for s in data.get("streams", []))
            return info
    # Fallback: parse ffmpeg -i output.
    result = subprocess.run([ffmpeg_binary(), "-hide_banner", "-i", path], capture_output=True, text=True, check=False)
    text = result.stderr
    import re

    match = re.search(r"Video: (\w+).*?(\d{2,5})x(\d{2,5}).*?([\d.]+) fps", text)
    if match is None:
        match = re.search(r"Video: (\w+).*?(\d{2,5})x(\d{2,5})", text)
        if match is None:
            raise RuntimeError("could not probe video: " + text[-400:])
        fps = 25.0
    else:
        fps = float(match.group(4))
    duration = 0.0
    pix = re.search(r"Video: \w+[^\n]*?, (\w+)\(([^)]*)\)", text)
    pix_fmt = pix.group(1) if pix else ""
    tags = [t.strip() for t in pix.group(2).split(",")] if pix else []
    color_range = next((t for t in tags if t in ("tv", "pc")), "")
    colour = [t for t in tags if t not in ("tv", "pc", "progressive", "top first", "bottom first")]
    color_space = color_transfer = color_primaries = ""
    if colour:
        parts = colour[0].split("/")
        color_primaries = parts[0]
        color_transfer = parts[1] if len(parts) > 1 else parts[0]
        color_space = parts[2] if len(parts) > 2 else parts[0]
    dmatch = re.search(r"Duration: (\d+):(\d+):([\d.]+)", text)
    if dmatch:
        duration = int(dmatch.group(1)) * 3600 + int(dmatch.group(2)) * 60 + float(dmatch.group(3))
    info.update(
        {
            "codec": match.group(1), "width": int(match.group(2)), "height": int(match.group(3)), "fps": fps,
            "fps_text": f"{fps:g}", "duration": duration, "frames": int(round(duration * fps)),
            "pix_fmt": pix_fmt, "color_transfer": color_transfer, "color_primaries": color_primaries, "color_space": color_space, "color_range": color_range,
            "has_audio": "Audio:" in text,
        }
    )
    return info


def _stream_info(video: dict, fmt: dict) -> dict:
    fps_text = video.get("avg_frame_rate") or video.get("r_frame_rate") or "25/1"
    num, den = fps_text.split("/") if "/" in fps_text else (fps_text, "1")
    fps = float(num) / float(den) if float(den) != 0 else 25.0
    duration = float(video.get("duration") or fmt.get("duration") or 0.0)
    frames = int(video.get("nb_frames") or 0)
    if frames <= 0 and duration > 0:
        frames = int(round(duration * fps))
    return {
        "codec": video.get("codec_name", ""),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": fps,
        "fps_text": fps_text,
        "duration": duration,
        "frames": frames,
        "pix_fmt": video.get("pix_fmt", ""),
        "color_transfer": video.get("color_transfer", "") or "",
        "color_primaries": video.get("color_primaries", "") or "",
        "color_space": video.get("color_space", "") or "",
        "color_range": video.get("color_range", "") or "",
    }


def guess_input_colour(info: dict) -> tuple[str, str]:
    """Map container colour tags to the studio's transfer / gamut identifiers."""
    trc = (info.get("color_transfer") or "").lower()
    prim = (info.get("color_primaries") or "").lower()
    transfer = {
        "bt709": "bt709", "smpte170m": "bt709", "bt470bg": "bt709", "iec61966-2-1": "srgb", "iec61966_2_1": "srgb",
        "arib-std-b67": "hlg", "smpte2084": "pq", "linear": "linear", "bt470m": "gamma22", "gamma22": "gamma22",
    }.get(trc, "bt709")
    gamut = {"bt2020": "bt2020", "smpte432": "p3d65", "bt709": "rec709"}.get(prim, "rec709")
    return transfer, gamut


class FrameReader:
    """Decode frames as 16-bit RGB through swscale with the right YUV matrix."""

    def __init__(self, path: str | Path, info: dict, start_frame: int = 0, frames: int | None = None, width: int | None = None, height: int | None = None) -> None:
        self.path = str(path)
        self.width = int(width or info["width"])
        self.height = int(height or info["height"])
        self.frames = frames
        fps = float(info.get("fps") or 25.0)
        matrix = info.get("color_space") or ("bt709" if info["height"] >= 600 else "bt601")
        matrix = {"bt470bg": "bt601", "smpte170m": "bt601", "bt2020nc": "bt2020", "bt2020c": "bt2020"}.get(matrix, matrix)
        if matrix not in ("bt709", "bt601", "bt2020", "smpte240m", "fcc"):
            matrix = "bt709"
        rng = info.get("color_range") or "tv"
        rng = "pc" if rng in ("pc", "full", "jpeg") else "tv"
        filters = [f"scale={self.width}:{self.height}:in_color_matrix={matrix}:in_range={rng}:out_range=pc:flags=lanczos"]
        command = [ffmpeg_binary(), "-v", "error", "-nostdin"]
        if start_frame > 0:
            command += ["-ss", f"{start_frame / fps:.6f}"]
        command += ["-i", self.path, "-map", "0:v:0", "-vf", ",".join(filters), "-pix_fmt", "rgb48le", "-f", "rawvideo"]
        if frames is not None:
            command += ["-frames:v", str(int(frames))]
        command += ["pipe:1"]
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.frame_bytes = self.width * self.height * 6

    def __iter__(self):
        return self

    def __next__(self) -> np.ndarray:
        assert self.process.stdout is not None
        buffer = bytearray()
        while len(buffer) < self.frame_bytes:
            chunk = self.process.stdout.read(self.frame_bytes - len(buffer))
            if not chunk:
                self.close()
                raise StopIteration
            buffer.extend(chunk)
        frame = np.frombuffer(bytes(buffer), dtype=np.uint16).reshape(self.height, self.width, 3)
        return frame.astype(np.float32) / 65535.0

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        try:
            self.process.stdout.close()  # type: ignore[union-attr]
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def read_single_frame(path: str | Path, info: dict, frame_index: int, width: int | None = None, height: int | None = None) -> np.ndarray:
    with FrameReader(path, info, frame_index, 1, width, height) as reader:
        for frame in reader:
            return frame
    raise RuntimeError(f"frame {frame_index} could not be decoded")


CODECS = {
    "prores4444": {"label": "ProRes 4444 (.mov)", "ext": ".mov", "args": ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuv444p10le", "-bits_per_mb", "8192", "-vendor", "apl0"]},
    "proreshq": {"label": "ProRes 422 HQ (.mov)", "ext": ".mov", "args": ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-bits_per_mb", "8192", "-vendor", "apl0"]},
    "h264": {"label": "H.264 high quality (.mp4)", "ext": ".mp4", "args": ["-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]},
    "h265": {"label": "H.265 10-bit (.mp4)", "ext": ".mp4", "args": ["-c:v", "libx265", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p10le", "-tag:v", "hvc1", "-movflags", "+faststart"]},
    "png16": {"label": "16-bit PNG sequence", "ext": "", "args": ["-c:v", "png", "-pix_fmt", "rgb48be"]},
    "dpx10": {"label": "10-bit Cineon DPX sequence (printing density)", "ext": "", "args": ["-c:v", "dpx", "-pix_fmt", "gbrp10le"]},
}


class FrameWriter:
    """Encode float linear or code frames through ffmpeg."""

    def __init__(self, output: str | Path, width: int, height: int, fps_text: str, codec: str, transfer: str = "bt1886", source_audio: str | None = None) -> None:
        self.output = Path(output)
        self.width, self.height = int(width), int(height)
        self.codec = codec
        spec = CODECS[codec]
        self.sequence = spec["ext"] == ""
        if self.sequence:
            self.output.mkdir(parents=True, exist_ok=True)
            target = str(self.output / ("%06d.dpx" if codec == "dpx10" else "%06d.png"))
        else:
            self.output.parent.mkdir(parents=True, exist_ok=True)
            target = str(self.output)
        in_fmt = "gbrp10le" if codec == "dpx10" else "rgb48le"
        command = [ffmpeg_binary(), "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", in_fmt, "-s", f"{self.width}x{self.height}", "-r", fps_text, "-i", "pipe:0"]
        self.audio = bool(source_audio) and not self.sequence
        if self.audio:
            command += ["-i", str(source_audio), "-map", "0:v:0", "-map", "1:a:0?", "-c:a", "aac" if codec in ("h264", "h265") else "pcm_s16le", "-shortest"]
        command += spec["args"]
        if not self.sequence:
            trc = "iec61966-2-1" if transfer == "srgb" else "bt709"
            command += ["-color_primaries", "bt709", "-color_trc", trc, "-colorspace", "bt709", "-color_range", "pc" if codec.startswith("prores") else "tv"]
        command += [target]
        self.command = command
        self._stderr = tempfile.TemporaryFile()
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=self._stderr)
        self.written = 0

    def write_encoded(self, encoded_unit: np.ndarray) -> None:
        """Write a display-encoded [0,1] RGB frame as 16-bit."""
        assert self.process.stdin is not None
        data = np.clip(np.rint(np.asarray(encoded_unit, dtype=np.float32) * 65535.0), 0, 65535).astype("<u2")
        self.process.stdin.write(np.ascontiguousarray(data).tobytes())
        self.written += 1

    def write_code10(self, code: np.ndarray) -> None:
        """Write exact 10-bit RGB code values (planar G, B, R for gbrp10le)."""
        assert self.process.stdin is not None
        c = np.asarray(code).astype("<u2")
        planes = np.concatenate([c[..., 1].ravel(), c[..., 2].ravel(), c[..., 0].ravel()])
        self.process.stdin.write(np.ascontiguousarray(planes).tobytes())
        self.written += 1

    def close(self) -> None:
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                pass
        self.process.wait()
        if self.codec == "dpx10" and self.process.returncode == 0:
            # Cineon printing density: transfer 1 / colorimetric 1 (SMPTE 268M),
            # which FFmpeg's DPX encoder does not write itself.
            for frame_path in sorted(self.output.glob("*.dpx")):
                with open(frame_path, "r+b") as handle:
                    head = handle.read(4)
                    if head in (b"SDPX", b"XPDS"):
                        handle.seek(801)
                        handle.write(bytes([1, 1]))
        self._stderr.seek(0)
        err = self._stderr.read()
        self._stderr.close()
        if self.process.returncode not in (0, None):
            raise RuntimeError("ffmpeg encode failed: " + err.decode("utf-8", "replace")[-800:])

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if exc[0] is None:
            self.close()
        else:
            try:
                self.process.kill()
            except Exception:
                pass


def write_png(path: str | Path, encoded_unit: np.ndarray) -> None:
    import cv2

    data = np.clip(np.rint(np.asarray(encoded_unit, dtype=np.float32) * 65535.0), 0, 65535).astype(np.uint16)
    cv2.imwrite(str(path), cv2.cvtColor(data, cv2.COLOR_RGB2BGR))


def encode_jpeg(encoded_unit: np.ndarray, quality: int = 92) -> bytes:
    import cv2

    data = np.clip(np.rint(np.asarray(encoded_unit, dtype=np.float32) * 255.0), 0, 255).astype(np.uint8)
    ok, buffer = cv2.imencode(".jpg", cv2.cvtColor(data, cv2.COLOR_RGB2BGR), [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("jpeg encode failed")
    return buffer.tobytes()
