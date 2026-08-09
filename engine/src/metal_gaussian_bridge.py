"""ctypes bridge for selective large-kernel Gaussian work on Apple Metal."""

from __future__ import annotations

import ctypes
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np


SOURCE = Path(__file__).with_suffix(".mm")
LIBRARY = Path("/tmp/libv27_metal_gaussian.dylib")
_BRIDGE = None
_STRIDED_BRIDGE = None
_ASYNC_SUBMIT = None
_ASYNC_WAIT = None
_REFERENCE = cv2.GaussianBlur
STATS = {
    "calls": 0,
    "strided_calls": 0,
    "bridge_seconds": 0.0,
    "wall_seconds": 0.0,
    "fallback_calls": 0,
}


def load_bridge():
    global _BRIDGE, _STRIDED_BRIDGE, _ASYNC_SUBMIT, _ASYNC_WAIT
    if _BRIDGE is not None:
        return _BRIDGE
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
    function = library.metal_gaussian_f32
    pointer = ctypes.POINTER(ctypes.c_float)
    function.argtypes = [
        pointer,
        pointer,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        pointer,
        ctypes.c_int,
        ctypes.c_int,
    ]
    function.restype = ctypes.c_double
    strided = library.metal_gaussian_strided_f32
    strided.argtypes = [
        pointer,
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        pointer,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        pointer,
        ctypes.c_int,
        ctypes.c_int,
    ]
    strided.restype = ctypes.c_double
    async_submit = library.metal_gaussian_submit_f32
    async_submit.argtypes = [
        pointer,
        pointer,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        pointer,
        ctypes.c_int,
        ctypes.c_int,
    ]
    async_submit.restype = ctypes.c_void_p
    async_wait = library.metal_gaussian_wait
    async_wait.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double)]
    async_wait.restype = ctypes.c_int
    _BRIDGE = function
    _STRIDED_BRIDGE = strided
    _ASYNC_SUBMIT = async_submit
    _ASYNC_WAIT = async_wait
    return function


def aligned_empty(shape, dtype=np.float32, page: int = 16_384) -> np.ndarray:
    """Allocate a contiguous NumPy view whose first byte is page-aligned."""
    target_dtype = np.dtype(dtype)
    count = int(np.prod(shape))
    extra = page // target_dtype.itemsize
    owner = np.empty(count + extra, dtype=target_dtype)
    byte_offset = (-owner.ctypes.data) % page
    item_offset = byte_offset // target_dtype.itemsize
    result = owner[item_offset : item_offset + count].reshape(shape)
    if result.ctypes.data % page != 0:
        raise RuntimeError("failed to allocate a page-aligned NumPy view")
    return result


class AsyncGaussianFlight:
    """Own the no-copy arrays until a submitted Metal command completes."""

    def __init__(self, handle, source, output, weights, submitted_at):
        self._handle = handle
        self.source = source
        self.output = output
        self.weights = weights
        self.submitted_at = submitted_at
        self.bridge_seconds: float | None = None

    def wait(self) -> np.ndarray:
        if self._handle is None:
            return self.output
        elapsed = ctypes.c_double()
        assert _ASYNC_WAIT is not None
        result = _ASYNC_WAIT(self._handle, ctypes.byref(elapsed))
        self._handle = None
        self.bridge_seconds = float(elapsed.value)
        if result != 0:
            raise RuntimeError(f"asynchronous Metal Gaussian failed: {result}")
        return self.output

    def __del__(self):
        if getattr(self, "_handle", None) is not None:
            try:
                self.wait()
            except Exception:
                pass


def submit_gaussian_async(
    source: np.ndarray,
    sigma: float,
    border: int = cv2.BORDER_REFLECT,
) -> AsyncGaussianFlight:
    """Submit one per-flight Gaussian while preserving no-copy lifetimes."""
    array = np.asarray(source, dtype=np.float32)
    channels = 1 if array.ndim == 2 else array.shape[2] if array.ndim == 3 else 0
    if channels not in (1, 2, 3, 4):
        raise ValueError("async Metal Gaussian supports one to four channels")
    if int(border) not in (cv2.BORDER_REFLECT, cv2.BORDER_REFLECT_101):
        raise ValueError("unsupported Metal border mode")
    page = 16_384
    if array.nbytes % page != 0:
        raise ValueError("async no-copy array length must be page-sized")
    if not array.flags.c_contiguous or array.ctypes.data % page != 0:
        aligned_source = aligned_empty(array.shape)
        np.copyto(aligned_source, array)
        array = aligned_source
    output = aligned_empty(array.shape)
    size = automatic_kernel_size(float(sigma))
    radius = size // 2
    weights = cv2.getGaussianKernel(
        size, float(sigma), cv2.CV_32F
    ).reshape(-1)
    load_bridge()
    assert _ASYNC_SUBMIT is not None
    pointer = ctypes.POINTER(ctypes.c_float)
    submitted_at = time.perf_counter()
    handle = _ASYNC_SUBMIT(
        array.ctypes.data_as(pointer),
        output.ctypes.data_as(pointer),
        int(array.shape[1]),
        int(array.shape[0]),
        channels,
        weights.ctypes.data_as(pointer),
        radius,
        int(border),
    )
    if not handle:
        raise RuntimeError("asynchronous Metal Gaussian submission failed")
    return AsyncGaussianFlight(
        handle, array, output, weights, submitted_at
    )


def root_array(array: np.ndarray) -> np.ndarray:
    root = array
    while isinstance(root.base, np.ndarray):
        root = root.base
    return root


def automatic_kernel_size(sigma: float) -> int:
    return max(1, int(round(float(sigma) * 8.0 + 1.0)) | 1)


def gaussian_blur(
    source,
    ksize,
    sigma_x,
    *positional,
    **keywords,
):
    sigma_y = keywords.get("sigmaY", 0.0)
    border = keywords.get("borderType", cv2.BORDER_DEFAULT)
    array = np.asarray(source)
    channels = 1 if array.ndim == 2 else array.shape[2] if array.ndim == 3 else 0
    eligible = (
        array.dtype == np.float32
        and channels in (1, 3)
        and array.shape[0] * array.shape[1] >= 1_000_000
        and float(sigma_x) >= 1.5
        and (float(sigma_y) == 0.0 or float(sigma_y) == float(sigma_x))
        and int(border) in (cv2.BORDER_REFLECT, cv2.BORDER_REFLECT_101)
        and not positional
    )
    if not eligible:
        STATS["fallback_calls"] += 1
        return _REFERENCE(source, ksize, sigma_x, *positional, **keywords)
    width, height = int(array.shape[1]), int(array.shape[0])
    size = (
        automatic_kernel_size(float(sigma_x))
        if tuple(ksize) == (0, 0)
        else int(ksize[0])
    )
    radius = size // 2
    weights = cv2.getGaussianKernel(size, float(sigma_x), cv2.CV_32F).reshape(-1)
    output = np.empty(array.shape, dtype=np.float32, order="C")
    pointer = ctypes.POINTER(ctypes.c_float)
    started = time.perf_counter()
    load_bridge()
    root = root_array(array)
    page = 16_384
    can_use_strided = (
        array.flags.c_contiguous
        and root.dtype == np.float32
        and root.flags.c_contiguous
        and root.ctypes.data % page == 0
        and root.nbytes % page == 0
        and output.ctypes.data % page == 0
        and output.nbytes % page == 0
        and all(stride % 4 == 0 for stride in array.strides)
    )
    if can_use_strided:
        offset = (array.ctypes.data - root.ctypes.data) // 4
        row_stride = array.strides[0] // 4
        pixel_stride = array.strides[1] // 4
        channel_stride = 1 if array.ndim == 2 else array.strides[2] // 4
        assert _STRIDED_BRIDGE is not None
        bridge_seconds = _STRIDED_BRIDGE(
            root.ctypes.data_as(pointer),
            root.nbytes,
            offset,
            row_stride,
            pixel_stride,
            channel_stride,
            output.ctypes.data_as(pointer),
            width,
            height,
            channels,
            weights.ctypes.data_as(pointer),
            radius,
            int(border),
        )
        if bridge_seconds >= 0.0:
            STATS["strided_calls"] += 1
    else:
        bridge_seconds = -20.0
    if bridge_seconds < 0.0:
        contiguous = np.ascontiguousarray(array, dtype=np.float32)
        bridge_seconds = _BRIDGE(
            contiguous.ctypes.data_as(pointer),
            output.ctypes.data_as(pointer),
            width,
            height,
            channels,
            weights.ctypes.data_as(pointer),
            radius,
            int(border),
        )
    wall = time.perf_counter() - started
    if bridge_seconds < 0.0:
        raise RuntimeError(f"Metal Gaussian bridge failed: {bridge_seconds}")
    STATS["calls"] += 1
    STATS["bridge_seconds"] += bridge_seconds
    STATS["wall_seconds"] += wall
    return output


def install() -> None:
    function = load_bridge()
    source = np.zeros((4, 4), dtype=np.float32)
    output = np.empty_like(source)
    weights = cv2.getGaussianKernel(13, 1.5, cv2.CV_32F).reshape(-1)
    pointer = ctypes.POINTER(ctypes.c_float)
    result = function(
        source.ctypes.data_as(pointer),
        output.ctypes.data_as(pointer),
        4,
        4,
        1,
        weights.ctypes.data_as(pointer),
        6,
        int(cv2.BORDER_REFLECT),
    )
    if result < 0.0:
        raise RuntimeError(f"Metal Gaussian bridge warm-up failed: {result}")
    cv2.GaussianBlur = gaussian_blur


def uninstall() -> None:
    cv2.GaussianBlur = _REFERENCE
