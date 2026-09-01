#!/usr/bin/env python3
"""Local web application for the 5279 studio.

    python3 studio/app.py            # opens http://127.0.0.1:8765

The server is standard-library only.  Rendering uses the ``film5279`` package
(NumPy / OpenCV / Numba) and FFmpeg for decode and encode.  Exports run in a
process pool so a multi-core machine renders several frames at once.
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import mimetypes
import multiprocessing
import os
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np

STUDIO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(STUDIO_ROOT))

from film5279 import FILM_GAUGES, PRESETS, FilmParams, decode_to_scene_linear, encode_display, render_frame  # noqa: E402
from film5279.colour import GAMUT_LABELS, TRANSFER_LABELS  # noqa: E402
from film5279.video import CODECS, FrameReader, FrameWriter, encode_jpeg, guess_input_colour, probe, read_single_frame  # noqa: E402

WORK_ROOT = Path(os.environ.get("FILM5279_WORK", STUDIO_ROOT / "work"))
UPLOAD_ROOT = WORK_ROOT / "uploads"
EXPORT_ROOT = WORK_ROOT / "exports"
UI_ROOT = STUDIO_ROOT / "ui"

_STATE_LOCK = threading.Lock()
SOURCES: dict[str, dict] = {}
JOBS: dict[str, dict] = {}
ENGINE = {"ready": False, "message": "starting", "progress": 0.0, "error": None}


# ---------------------------------------------------------------------------
# Engine bootstrap (lattices + observer calibration)
# ---------------------------------------------------------------------------


def _bootstrap_engine() -> None:
    try:
        from film5279 import spectral
        from film5279.observers import observers

        def progress(i, n):
            ENGINE["progress"] = i / n
            ENGINE["message"] = f"building V87 spectral lattice {i}/{n}"

        ENGINE["message"] = "loading spectral lattices"
        spectral.spectral_model(progress)
        ENGINE["message"] = "calibrating observers"
        observers()
        ENGINE["ready"] = True
        ENGINE["message"] = "ready"
        ENGINE["progress"] = 1.0
    except Exception as error:  # pragma: no cover
        ENGINE["error"] = f"{error}\n{traceback.format_exc()}"
        ENGINE["message"] = "engine failed"


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _preview_size(info: dict, width: int) -> tuple[int, int]:
    width = max(64, min(int(width), info["width"]))
    width -= width % 2
    height = max(2, round(info["height"] * width / info["width"]))
    height -= height % 2
    return width, height


def render_preview(source: dict, frame_index: int, params: FilmParams, width: int, views: list[str], mode: str, crop: tuple[float, float]) -> dict:
    info = source["info"]
    started = time.perf_counter()
    if mode == "crop":
        full = read_single_frame(source["path"], info, frame_index)
        cw, ch = _preview_size(info, width)
        cw, ch = min(cw, info["width"]), min(ch, info["height"])
        x0 = int(round(np.clip(crop[0], 0.0, 1.0) * (info["width"] - cw)))
        y0 = int(round(np.clip(crop[1], 0.0, 1.0) * (info["height"] - ch)))
        encoded = np.ascontiguousarray(full[y0 : y0 + ch, x0 : x0 + cw])
        reference_width = info["width"]
    else:
        pw, ph = _preview_size(info, width)
        encoded = read_single_frame(source["path"], info, frame_index, pw, ph)
        reference_width = None
    decode_seconds = time.perf_counter() - started
    scene = decode_to_scene_linear(encoded, params)
    want = tuple(v for v in views if v in ("projection", "scan", "negative"))
    result = render_frame(scene, frame_index, params, want=want, reference_width=reference_width)
    images = {}
    if "source" in views:
        images["source"] = base64.b64encode(encode_jpeg(encoded)).decode("ascii")
    for name in want:
        image = getattr(result, name)
        if image is not None:
            images[name] = base64.b64encode(encode_jpeg(encode_display(image, "srgb"))).decode("ascii")
    return {
        "frame": frame_index,
        "width": int(encoded.shape[1]),
        "height": int(encoded.shape[0]),
        "images": images,
        "seconds": {**{k: round(v, 3) for k, v in result.seconds.items()}, "decode": round(decode_seconds, 3)},
    }


# ---------------------------------------------------------------------------
# Export jobs
# ---------------------------------------------------------------------------

_WORKER_PARAMS: dict = {}


def _worker_init(cv_threads: int) -> None:
    import cv2

    cv2.setNumThreads(cv_threads)
    try:
        import numba

        numba.set_num_threads(max(1, cv_threads))
    except Exception:
        pass
    from film5279 import spectral
    from film5279.observers import observers

    spectral.spectral_model()
    observers()


def _worker_render(task: tuple) -> tuple:
    frame_index, encoded, params_dict, outputs, output_transfer = task
    params = FilmParams.from_dict(params_dict)
    scene = decode_to_scene_linear(encoded, params)
    want = tuple(o for o in outputs if o in ("projection", "scan")) + (("cineon",) if "dpx" in outputs else ())
    result = render_frame(scene, frame_index, params, want=want)
    payload = {}
    if "projection" in outputs:
        payload["projection"] = np.clip(np.rint(encode_display(result.projection, output_transfer) * 65535.0), 0, 65535).astype("<u2")
    if "scan" in outputs:
        payload["scan"] = np.clip(np.rint(encode_display(result.scan, output_transfer) * 65535.0), 0, 65535).astype("<u2")
    if "dpx" in outputs:
        payload["dpx"] = result.cineon_code
    return frame_index, payload, result.seconds.get("total", 0.0)


def run_export_job(job: dict) -> None:
    source = SOURCES[job["source"]]
    info = source["info"]
    params = FilmParams.from_dict(job["params"])
    outputs = job["outputs"]
    start, end = job["start"], job["end"]
    total = end - start + 1
    job_dir = Path(job["out_dir"])
    job_dir.mkdir(parents=True, exist_ok=True)
    stem = job["name"]
    codec = job["codec"]
    writers: dict[str, FrameWriter] = {}
    try:
        for output in outputs:
            if output == "dpx":
                writers["dpx"] = FrameWriter(job_dir / f"{stem}_cineon_dpx", info["width"], info["height"], info["fps_text"], "dpx10")
            else:
                spec = CODECS[codec]
                suffix = {"projection": "2383_print", "scan": "bluray_scan"}[output]
                target = job_dir / (f"{stem}_{suffix}{spec['ext']}" if spec["ext"] else f"{stem}_{suffix}_png16")
                writers[output] = FrameWriter(target, info["width"], info["height"], info["fps_text"], codec, params.output_transfer, source["path"] if job.get("audio", True) else None)
        job["files"] = [str(w.output) for w in writers.values()]
        workers = max(1, int(job.get("workers") or 1))
        # "spawn" gives every worker a fresh interpreter: forking a process that
        # already runs Numba/OpenCV/HTTP threads can deadlock on inherited locks.
        context = multiprocessing.get_context("spawn")
        pool = concurrent.futures.ProcessPoolExecutor(max_workers=workers, mp_context=context, initializer=_worker_init, initargs=(max(1, (os.cpu_count() or 2) // workers),))
        pending: dict[int, concurrent.futures.Future] = {}
        next_to_write = start
        started = time.perf_counter()
        frame_seconds = []
        with FrameReader(source["path"], info, start, total) as reader:
            frame_index = start
            for encoded in reader:
                if job["cancel"]:
                    break
                pending[frame_index] = pool.submit(_worker_render, (frame_index, encoded, params.to_dict(), outputs, params.output_transfer))
                frame_index += 1
                while len(pending) >= workers * 2 or (frame_index > end and pending):
                    future = pending.pop(next_to_write)
                    index, payload, seconds = future.result()
                    frame_seconds.append(seconds)
                    for name, data in payload.items():
                        if name == "dpx":
                            writers["dpx"].write_code10(data)
                        else:
                            writers[name].process.stdin.write(np.ascontiguousarray(data).tobytes())
                            writers[name].written += 1
                    next_to_write += 1
                    job["done"] = next_to_write - start
                    elapsed = time.perf_counter() - started
                    job["elapsed"] = elapsed
                    job["eta"] = elapsed / max(job["done"], 1) * (total - job["done"])
                    job["fps"] = job["done"] / max(elapsed, 1e-6)
                    if frame_index > end and not pending:
                        break
        while pending and not job["cancel"]:
            future = pending.pop(next_to_write)
            index, payload, seconds = future.result()
            for name, data in payload.items():
                if name == "dpx":
                    writers["dpx"].write_code10(data)
                else:
                    writers[name].process.stdin.write(np.ascontiguousarray(data).tobytes())
                    writers[name].written += 1
            next_to_write += 1
            job["done"] = next_to_write - start
        pool.shutdown(wait=True, cancel_futures=True)
        for writer in writers.values():
            writer.close()
        job["status"] = "cancelled" if job["cancel"] else "done"
        job["elapsed"] = time.perf_counter() - started
        job["mean_frame_seconds"] = float(np.mean(frame_seconds)) if frame_seconds else 0.0
    except Exception as error:
        job["status"] = "failed"
        job["error"] = f"{error}\n{traceback.format_exc()[-1500:]}"
        for writer in writers.values():
            try:
                writer.process.kill()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------


def _json(handler: BaseHTTPRequestHandler, status: int, payload) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _register_source(path: Path) -> dict:
    info = probe(path)
    transfer, gamut = guess_input_colour(info)
    source_id = uuid.uuid4().hex[:10]
    entry = {"id": source_id, "path": str(path), "name": path.name, "info": info, "guess": {"input_transfer": transfer, "input_gamut": gamut}}
    with _STATE_LOCK:
        SOURCES[source_id] = entry
    return entry


class Handler(BaseHTTPRequestHandler):
    server_version = "film5279-studio/1.0"

    def log_message(self, format, *args):  # noqa: A002 - quieter console
        if os.environ.get("FILM5279_VERBOSE"):
            super().log_message(format, *args)

    # ---- helpers ----------------------------------------------------------
    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def _serve_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(path))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # ---- GET ----------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path in ("/", "/index.html"):
            return self._serve_file(UI_ROOT / "index.html")
        if url.path.startswith("/static/"):
            return self._serve_file(UI_ROOT / url.path[len("/static/") :])
        if url.path == "/api/meta":
            return _json(self, 200, {
                "engine": ENGINE,
                "defaults": FilmParams().to_dict(),
                "presets": {k: {"label": v["label"], "params": v["params"]} for k, v in PRESETS.items()},
                "transfers": TRANSFER_LABELS,
                "gamuts": GAMUT_LABELS,
                "gauges": {k: v["label"] for k, v in FILM_GAUGES.items()},
                "codecs": {k: v["label"] for k, v in CODECS.items() if k != "dpx10"},
                "cpu_count": os.cpu_count(),
                "export_root": str(EXPORT_ROOT),
                "sources": list(SOURCES.values()),
            })
        if url.path == "/api/jobs":
            with _STATE_LOCK:
                jobs = [{k: v for k, v in job.items() if k != "params"} for job in JOBS.values()]
            return _json(self, 200, {"jobs": jobs})
        if url.path == "/api/thumb":
            source = SOURCES.get(query.get("source", ""))
            if source is None:
                return _json(self, 404, {"error": "unknown source"})
            frame = int(query.get("frame", 0))
            width, height = _preview_size(source["info"], int(query.get("width", 320)))
            try:
                encoded = read_single_frame(source["path"], source["info"], frame, width, height)
            except Exception as error:
                return _json(self, 500, {"error": str(error)})
            data = encode_jpeg(encoded, 80)
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if url.path == "/api/browse":
            root = Path(query.get("path") or Path.home()).expanduser()
            if not root.is_dir():
                root = root.parent if root.parent.is_dir() else Path.home()
            entries = []
            try:
                for child in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                    if child.name.startswith("."):
                        continue
                    if child.is_dir():
                        entries.append({"name": child.name, "path": str(child), "dir": True})
                    elif child.suffix.lower() in (".mov", ".mp4", ".mxf", ".mkv", ".avi", ".m4v", ".webm", ".mts", ".m2ts", ".prores", ".braw", ".r3d", ".dng", ".exr", ".tif", ".tiff", ".png", ".jpg", ".jpeg"):
                        entries.append({"name": child.name, "path": str(child), "dir": False, "size": child.stat().st_size})
            except PermissionError:
                pass
            return _json(self, 200, {"path": str(root), "parent": str(root.parent), "entries": entries})
        self.send_error(404)

    # ---- POST ---------------------------------------------------------------
    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        try:
            if url.path == "/api/open":
                body = self._read_json()
                path = Path(body.get("path", "")).expanduser()
                if not path.is_file():
                    return _json(self, 400, {"error": f"not a file: {path}"})
                return _json(self, 200, {"source": _register_source(path)})
            if url.path == "/api/upload":
                name = Path(self.headers.get("X-File-Name", "upload.bin")).name
                length = int(self.headers.get("Content-Length") or 0)
                UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
                target = UPLOAD_ROOT / f"{uuid.uuid4().hex[:6]}_{name}"
                with open(target, "wb") as handle:
                    remaining = length
                    while remaining > 0:
                        chunk = self.rfile.read(min(1 << 20, remaining))
                        if not chunk:
                            break
                        handle.write(chunk)
                        remaining -= len(chunk)
                return _json(self, 200, {"source": _register_source(target)})
            if url.path == "/api/preview":
                if not ENGINE["ready"]:
                    return _json(self, 503, {"error": "engine not ready", "engine": ENGINE})
                body = self._read_json()
                source = SOURCES.get(body.get("source", ""))
                if source is None:
                    return _json(self, 404, {"error": "unknown source"})
                params = FilmParams.from_dict(body.get("params", {}))
                frame = int(np.clip(int(body.get("frame", 0)), 0, max(source["info"]["frames"] - 1, 0)))
                result = render_preview(
                    source, frame, params, int(body.get("width", 960)),
                    list(body.get("views", ["projection", "scan"])), body.get("mode", "fit"),
                    (float(body.get("crop_x", 0.5)), float(body.get("crop_y", 0.5))),
                )
                return _json(self, 200, result)
            if url.path == "/api/export":
                if not ENGINE["ready"]:
                    return _json(self, 503, {"error": "engine not ready"})
                body = self._read_json()
                source = SOURCES.get(body.get("source", ""))
                if source is None:
                    return _json(self, 404, {"error": "unknown source"})
                params = FilmParams.from_dict(body.get("params", {}))
                frames = max(source["info"]["frames"], 1)
                start = int(np.clip(int(body.get("start", 0)), 0, frames - 1))
                end = int(np.clip(int(body.get("end", frames - 1)), start, frames - 1))
                outputs = [o for o in body.get("outputs", ["projection", "scan"]) if o in ("projection", "scan", "dpx")]
                if not outputs:
                    return _json(self, 400, {"error": "choose at least one output"})
                codec = body.get("codec", "prores4444")
                if codec not in CODECS or codec == "dpx10":
                    return _json(self, 400, {"error": "unknown codec"})
                out_dir = Path(body.get("out_dir") or EXPORT_ROOT).expanduser()
                name = "".join(ch for ch in (body.get("name") or Path(source["name"]).stem) if ch.isalnum() or ch in "-_ .").strip() or "film5279"
                job = {
                    "id": uuid.uuid4().hex[:8], "source": source["id"], "source_name": source["name"], "params": params.to_dict(),
                    "outputs": outputs, "codec": codec, "out_dir": str(out_dir), "name": name, "start": start, "end": end,
                    "total": end - start + 1, "done": 0, "status": "running", "cancel": False, "elapsed": 0.0, "eta": None,
                    "fps": 0.0, "files": [], "error": None, "audio": bool(body.get("audio", True)),
                    "workers": int(body.get("workers") or max(1, (os.cpu_count() or 4) // 4)), "created": time.time(),
                }
                with _STATE_LOCK:
                    JOBS[job["id"]] = job
                threading.Thread(target=run_export_job, args=(job,), daemon=True).start()
                return _json(self, 200, {"job": {k: v for k, v in job.items() if k != "params"}})
            if url.path == "/api/jobs/cancel":
                body = self._read_json()
                job = JOBS.get(body.get("id", ""))
                if job is None:
                    return _json(self, 404, {"error": "unknown job"})
                job["cancel"] = True
                return _json(self, 200, {"ok": True})
            if url.path == "/api/jobs/clear":
                with _STATE_LOCK:
                    for key in [k for k, j in JOBS.items() if j["status"] != "running"]:
                        JOBS.pop(key)
                return _json(self, 200, {"ok": True})
        except Exception as error:
            return _json(self, 500, {"error": str(error), "trace": traceback.format_exc()[-2000:]})
        self.send_error(404)


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=_bootstrap_engine, daemon=True).start()
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    url = f"http://{host}:{port}/"
    print(f"5279 studio  ->  {url}", flush=True)
    if open_browser:
        try:
            import webbrowser

            threading.Timer(0.8, lambda: webbrowser.open(url)).start()
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kodak 5279 film studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    serve(args.host, args.port, not args.no_browser)
