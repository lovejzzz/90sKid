"""Research bridge for exact-distribution Philox/Metal binomial sampling."""

from __future__ import annotations

import ctypes
import subprocess
import time
from pathlib import Path

import numpy as np


SOURCE = Path(__file__).with_suffix(".mm")
LIBRARY = Path("/tmp/libv35_metal_binomial.dylib")
_FUNCTIONS = None
_ASYNC_SUBMIT = None
_ASYNC_WAIT = None
STATS = {"calls": 0, "bridge_seconds": 0.0, "wall_seconds": 0.0}


def load_bridge():
    global _FUNCTIONS, _ASYNC_SUBMIT, _ASYNC_WAIT
    if _FUNCTIONS is not None:
        return _FUNCTIONS
    if not LIBRARY.exists() or LIBRARY.stat().st_mtime < SOURCE.stat().st_mtime:
        subprocess.run(
            [
                "clang++",
                "-O3",
                "-dynamiclib",
                "-fobjc-arc",
                "-framework",
                "Foundation",
                "-framework",
                "Metal",
                str(SOURCE),
                "-o",
                str(LIBRARY),
            ],
            check=True,
        )
    library = ctypes.CDLL(str(LIBRARY))
    pointer = ctypes.POINTER(ctypes.c_float)
    functions = {}
    for mode, name in (
        ("inverse", "metal_binomial_f32"),
        ("bernoulli", "metal_binomial_bernoulli_f32"),
    ):
        function = getattr(library, name)
        function.argtypes = [
            pointer,
            pointer,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint64,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        function.restype = ctypes.c_double
        functions[mode] = function
    _FUNCTIONS = functions
    _ASYNC_SUBMIT = library.metal_binomial_submit_f32
    _ASYNC_SUBMIT.argtypes = [
        pointer,
        pointer,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint64,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_uint32,
    ]
    _ASYNC_SUBMIT.restype = ctypes.c_void_p
    _ASYNC_WAIT = library.metal_binomial_wait
    _ASYNC_WAIT.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
    _ASYNC_WAIT.restype = ctypes.c_int
    return functions


def aligned_empty(shape, dtype=np.float32, page: int = 16_384) -> np.ndarray:
    target_dtype = np.dtype(dtype)
    count = int(np.prod(shape))
    owner = np.empty(count + page // target_dtype.itemsize, dtype=target_dtype)
    item_offset = ((-owner.ctypes.data) % page) // target_dtype.itemsize
    return owner[item_offset : item_offset + count].reshape(shape)


class AsyncBinomialFlight:
    def __init__(self, handle, source, output, submitted_at):
        self._handle = handle
        self.source = source
        self.output = output
        self.submitted_at = submitted_at
        self.bridge_seconds = None

    def wait(self) -> np.ndarray:
        if self._handle is None:
            return self.output
        elapsed = ctypes.c_double()
        result = _ASYNC_WAIT(self._handle, ctypes.byref(elapsed))
        self._handle = None
        self.bridge_seconds = float(elapsed.value)
        if result != 0:
            raise RuntimeError(f"asynchronous Metal binomial failed: {result}")
        STATS["calls"] += 1
        STATS["bridge_seconds"] += self.bridge_seconds
        STATS["wall_seconds"] += time.perf_counter() - self.submitted_at
        return self.output

    def __del__(self):
        if getattr(self, "_handle", None) is not None:
            try:
                self.wait()
            except Exception:
                pass


def submit(
    probability: np.ndarray,
    trials: int,
    seed: int,
    *,
    origin: tuple[int, int] = (0, 0),
    full_width: int | None = None,
    mode: str = "inverse",
) -> AsyncBinomialFlight:
    source_view = np.asarray(probability, dtype=np.float32)
    if source_view.ndim != 2:
        raise ValueError("Metal binomial input must be a scalar 2D plane")
    source = aligned_empty(source_view.shape)
    np.copyto(source, source_view)
    output = aligned_empty(source.shape)
    origin_x, origin_y = origin
    global_width = source.shape[1] if full_width is None else int(full_width)
    if mode not in ("inverse", "bernoulli"):
        raise ValueError(f"unsupported Metal binomial mode: {mode}")
    load_bridge()
    pointer = ctypes.POINTER(ctypes.c_float)
    submitted_at = time.perf_counter()
    handle = _ASYNC_SUBMIT(
        source.ctypes.data_as(pointer),
        output.ctypes.data_as(pointer),
        source.size,
        int(trials),
        int(seed) & 0xFFFFFFFFFFFFFFFF,
        int(origin_x),
        int(origin_y),
        int(source.shape[1]),
        global_width,
        1 if mode == "bernoulli" else 0,
    )
    if not handle:
        raise RuntimeError("asynchronous Metal binomial submission failed")
    return AsyncBinomialFlight(handle, source, output, submitted_at)


def sample(
    probability: np.ndarray,
    trials: int,
    seed: int,
    mode: str = "bernoulli",
    *,
    origin: tuple[int, int] = (0, 0),
    full_width: int | None = None,
) -> np.ndarray:
    source = np.ascontiguousarray(probability, dtype=np.float32)
    output = np.empty_like(source)
    pointer = ctypes.POINTER(ctypes.c_float)
    if source.ndim != 2:
        raise ValueError("Metal binomial input must be a scalar 2D plane")
    origin_x, origin_y = origin
    global_width = source.shape[1] if full_width is None else int(full_width)
    started = time.perf_counter()
    bridge_seconds = load_bridge()[mode](
        source.ctypes.data_as(pointer),
        output.ctypes.data_as(pointer),
        source.size,
        int(trials),
        int(seed) & 0xFFFFFFFFFFFFFFFF,
        int(origin_x),
        int(origin_y),
        int(source.shape[1]),
        global_width,
    )
    if bridge_seconds < 0.0:
        raise RuntimeError(f"Metal binomial bridge failed: {bridge_seconds}")
    STATS["calls"] += 1
    STATS["bridge_seconds"] += float(bridge_seconds)
    STATS["wall_seconds"] += time.perf_counter() - started
    return output
