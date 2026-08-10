"""Research bridge for exact-distribution Philox/Metal binomial sampling."""

from __future__ import annotations

import collections
import ctypes
import math
import subprocess
import threading
import time
from pathlib import Path

import numpy as np


SOURCE = Path(__file__).with_suffix(".mm")
LIBRARY = Path("/tmp/libv35_metal_binomial.dylib")
_FUNCTIONS = None
_ASYNC_SUBMIT = None
_ASYNC_WAIT = None
STATS = {
    "calls": 0,
    "bridge_seconds": 0.0,
    "wall_seconds": 0.0,
    "tiled_calls": 0,
    "tile_dispatches": 0,
    "maximum_tile_pixels": 0,
    "tile_assembly_seconds": 0.0,
}


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


class AsyncTiledBinomialFlight:
    """Bounded row-wavefront submission with full-frame Philox coordinates.

    Only the point-sampling working set is tiled. The returned plane is still
    full frame so all downstream optical filters retain their established
    whole-frame border and floating-point contracts.
    """

    def __init__(
        self,
        probability: np.ndarray,
        trials: int,
        seed: int,
        workset_pixels: int,
        in_flight: int,
        mode: str,
    ) -> None:
        source = np.asarray(probability, dtype=np.float32)
        if source.ndim != 2:
            raise ValueError("Metal binomial input must be a scalar 2D plane")
        if workset_pixels < source.shape[1]:
            raise ValueError(
                "wavefront workset must hold at least one complete image row"
            )
        if in_flight < 1:
            raise ValueError("wavefront in-flight count must be positive")
        if source.flags.c_contiguous and source.ctypes.data % 16_384 == 0:
            self.source = source
        else:
            self.source = aligned_empty(source.shape)
            np.copyto(self.source, source)
        self.output = aligned_empty(source.shape)
        self.trials = int(trials)
        self.seed = int(seed)
        self.mode = mode
        self.in_flight = int(in_flight)
        requested_rows = max(1, int(workset_pixels) // source.shape[1])
        row_bytes = source.shape[1] * source.dtype.itemsize
        alignment_rows = 16_384 // math.gcd(16_384, row_bytes)
        self.rows_per_tile = (
            max(
                alignment_rows,
                requested_rows // alignment_rows * alignment_rows,
            )
            if requested_rows >= alignment_rows
            else requested_rows
        )
        self._next_row = 0
        self._failure: BaseException | None = None
        self._pending: collections.deque[
            tuple[int, int, AsyncBinomialFlight]
        ] = collections.deque()
        for _ in range(self.in_flight):
            if not self._submit_next():
                break
        self._feeder = threading.Thread(
            target=self._drain,
            name="v43h-metal-wavefront",
            daemon=True,
        )
        self._feeder.start()

    def _submit_next(self) -> bool:
        height, width = self.source.shape
        if self._next_row >= height:
            return False
        row0 = self._next_row
        row1 = min(row0 + self.rows_per_tile, height)
        flight = submit(
            self.source[row0:row1],
            self.trials,
            self.seed,
            origin=(0, row0),
            full_width=width,
            mode=self.mode,
            copy_source=False,
            output=self.output[row0:row1],
        )
        self._pending.append((row0, row1, flight))
        self._next_row = row1
        STATS["tile_dispatches"] += 1
        STATS["maximum_tile_pixels"] = max(
            int(STATS["maximum_tile_pixels"]), (row1 - row0) * width
        )
        return True

    def _drain(self) -> None:
        assembly_started = time.perf_counter()
        try:
            while self._pending:
                _row0, _row1, flight = self._pending.popleft()
                flight.wait()
                self._submit_next()
        except BaseException as error:
            self._failure = error
        finally:
            STATS["tiled_calls"] += 1
            STATS["tile_assembly_seconds"] += (
                time.perf_counter() - assembly_started
            )

    def wait(self) -> np.ndarray:
        self._feeder.join()
        if self._failure is not None:
            raise self._failure
        return self.output


def submit_tiled(
    probability: np.ndarray,
    trials: int,
    seed: int,
    *,
    workset_pixels: int,
    in_flight: int = 2,
    mode: str = "bernoulli",
) -> AsyncTiledBinomialFlight:
    """Submit a bounded full-row wavefront without changing random identity."""

    return AsyncTiledBinomialFlight(
        probability,
        trials,
        seed,
        int(workset_pixels),
        int(in_flight),
        mode,
    )


def submit(
    probability: np.ndarray,
    trials: int,
    seed: int,
    *,
    origin: tuple[int, int] = (0, 0),
    full_width: int | None = None,
    mode: str = "inverse",
    copy_source: bool = True,
    output: np.ndarray | None = None,
) -> AsyncBinomialFlight:
    source_input = np.asarray(probability)
    if not copy_source and source_input.dtype != np.float32:
        raise ValueError("zero-copy Metal binomial input must be float32")
    source_view = np.asarray(source_input, dtype=np.float32)
    if source_view.ndim != 2:
        raise ValueError("Metal binomial input must be a scalar 2D plane")
    if copy_source:
        source = aligned_empty(source_view.shape)
        np.copyto(source, source_view)
    else:
        if not source_view.flags.c_contiguous:
            raise ValueError("zero-copy Metal binomial input must be contiguous")
        source = source_view
    if output is None:
        output = aligned_empty(source.shape)
    else:
        output = np.asarray(output)
        if (
            output.dtype != np.float32
            or output.shape != source.shape
            or not output.flags.c_contiguous
        ):
            raise ValueError(
                "Metal binomial output must be matching contiguous float32"
            )
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
