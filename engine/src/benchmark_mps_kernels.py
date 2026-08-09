#!/usr/bin/env python3
"""Measure M4 Max MPS compute and transfer costs on one native frame."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as functional

import emulsion_experiment as e


def synchronize() -> None:
    torch.mps.synchronize()


def timed(function):
    synchronize()
    started = time.perf_counter()
    result = function()
    synchronize()
    return result, time.perf_counter() - started


def gaussian_kernel1d(sigma: float) -> torch.Tensor:
    radius = round(4.0 * sigma)
    positions = torch.arange(-radius, radius + 1, dtype=torch.float32)
    kernel = torch.exp(-0.5 * (positions / sigma) ** 2)
    return kernel / kernel.sum()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--log-exposure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS is unavailable")
    raw = np.asarray(np.load(args.raw, mmap_mode="r"), dtype=np.float32)
    matrix = np.array(
        [[0.6370, 0.1446, 0.1689], [0.2627, 0.6780, 0.0593], [0.0000, 0.0281, 1.0610]],
        dtype=np.float32,
    )
    cpu_reference_started = time.perf_counter()
    cpu_reference = cv2.transform(raw, matrix)
    cpu_matrix_seconds = time.perf_counter() - cpu_reference_started

    tensor, upload_seconds = timed(lambda: torch.from_numpy(raw).to("mps"))
    matrix_tensor = torch.from_numpy(matrix.T.copy()).to("mps")
    # Warm shader compilation separately from steady-state timing.
    warm = tensor[:16, :16] @ matrix_tensor
    synchronize()
    del warm
    transformed, gpu_matrix_seconds = timed(lambda: tensor @ matrix_tensor)
    candidate, download_seconds = timed(lambda: transformed.to("cpu").numpy())
    matrix_delta = np.abs(cpu_reference - candidate)

    sigma = 3.1
    cpu_blur_started = time.perf_counter()
    cpu_blur = cv2.GaussianBlur(raw, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
    cpu_blur_seconds = time.perf_counter() - cpu_blur_started
    nchw = tensor.permute(2, 0, 1).unsqueeze(0)
    kernel = gaussian_kernel1d(sigma).to("mps")
    radius = kernel.numel() // 2
    horizontal = kernel.reshape(1, 1, 1, -1).repeat(3, 1, 1, 1)
    vertical = kernel.reshape(1, 1, -1, 1).repeat(3, 1, 1, 1)
    warm = functional.conv2d(
        functional.pad(nchw[:, :, :16, :16], (radius, radius, radius, radius), mode="reflect"),
        horizontal,
        groups=3,
    )
    synchronize()
    del warm

    def gpu_blur():
        padded = functional.pad(nchw, (radius, radius, radius, radius), mode="reflect")
        horizontal_result = functional.conv2d(padded, horizontal, groups=3)
        return functional.conv2d(horizontal_result, vertical, groups=3)

    blurred, gpu_blur_seconds = timed(gpu_blur)
    blur_candidate, blur_download_seconds = timed(
        lambda: blurred.squeeze(0).permute(1, 2, 0).to("cpu").numpy()
    )
    blur_delta = np.abs(cpu_blur - blur_candidate)

    log_exposure = np.asarray(np.load(args.log_exposure, mmap_mode="r"), dtype=np.float32)
    cpu_record_started = time.perf_counter()
    cpu_record = e.record_densities_from_log_exposure(log_exposure)
    cpu_record_seconds = time.perf_counter() - cpu_record_started
    log_tensor, log_upload_seconds = timed(
        lambda: torch.from_numpy(log_exposure).to("mps")
    )
    sensito_axis = torch.from_numpy(e.SENSITO_LOG_EXPOSURE).to("mps")
    sensito_density = torch.from_numpy(e.SENSITO_DENSITY_RGB).to("mps")
    centres = torch.from_numpy(
        e.SUBEMULSION_FAST_CENTRE_LOGE_RGB[:, None]
        + e.SUBEMULSION_SPEED_OFFSETS_LOGE[None, :]
    ).to("mps")
    widths = torch.from_numpy(e.SUBEMULSION_TRANSITION_WIDTH_RGB[:, None]).to("mps")
    capacities = torch.from_numpy(e.SUBEMULSION_CAPACITY_FRACTIONS).to("mps")
    record_mix = torch.from_numpy(e.SUBEMULSION_DYE_RECORD_MIX).to("mps")

    def interpolate_channel(values: torch.Tensor, channel: int) -> torch.Tensor:
        upper = torch.searchsorted(sensito_axis, values.contiguous())
        upper = upper.clamp(1, sensito_axis.numel() - 1)
        lower = upper - 1
        axis0 = sensito_axis[lower]
        axis1 = sensito_axis[upper]
        value0 = sensito_density[channel, lower]
        value1 = sensito_density[channel, upper]
        fraction = (values - axis0) / (axis1 - axis0)
        interpolated = value0 + fraction * (value1 - value0)
        interpolated = torch.where(
            values <= sensito_axis[0], sensito_density[channel, 0], interpolated
        )
        return torch.where(
            values >= sensito_axis[-1], sensito_density[channel, -1], interpolated
        )

    def record_density_mps() -> torch.Tensor:
        density = torch.stack(
            [interpolate_channel(log_tensor[..., channel], channel) for channel in range(3)],
            dim=-1,
        )
        neutral_log = log_tensor.mean(dim=-1)
        neutral_density = torch.stack(
            [interpolate_channel(neutral_log, channel) for channel in range(3)],
            dim=-1,
        )
        activation = torch.sigmoid(
            ((log_tensor[..., :, None] - centres) / widths).clamp(-16.0, 16.0)
        )
        marginal = activation * (1.0 - activation) * capacities / widths
        marginal = marginal / marginal.sum(dim=-1, keepdim=True).clamp_min(1e-8)
        effective_mix = torch.einsum("...sp,pds->...ds", marginal, record_mix)
        departure = torch.einsum(
            "...s,...ds->...d", density - neutral_density, effective_mix
        )
        return neutral_density + departure

    warm = record_density_mps.__call__()
    synchronize()
    del warm
    gpu_record, gpu_record_seconds = timed(record_density_mps)
    record_candidate, record_download_seconds = timed(
        lambda: gpu_record.to("cpu").numpy()
    )
    record_delta = np.abs(cpu_record - record_candidate)

    result = {
        "shape": list(raw.shape),
        "upload_seconds": upload_seconds,
        "download_seconds": download_seconds,
        "matrix": {
            "opencv_cpu_seconds": cpu_matrix_seconds,
            "mps_compute_seconds": gpu_matrix_seconds,
            "mps_roundtrip_seconds": upload_seconds + gpu_matrix_seconds + download_seconds,
            "maximum_error": float(matrix_delta.max()),
            "mean_error": float(matrix_delta.mean()),
        },
        "gaussian_sigma": sigma,
        "gaussian": {
            "opencv_cpu_seconds": cpu_blur_seconds,
            "mps_compute_seconds": gpu_blur_seconds,
            "mps_download_seconds": blur_download_seconds,
            "mps_roundtrip_seconds": upload_seconds + gpu_blur_seconds + blur_download_seconds,
            "maximum_error": float(blur_delta.max()),
            "mean_error": float(blur_delta.mean()),
        },
        "record_density_mix": {
            "numpy_seconds": cpu_record_seconds,
            "mps_compute_seconds": gpu_record_seconds,
            "mps_upload_seconds": log_upload_seconds,
            "mps_download_seconds": record_download_seconds,
            "mps_roundtrip_seconds": (
                log_upload_seconds + gpu_record_seconds + record_download_seconds
            ),
            "maximum_error": float(record_delta.max()),
            "mean_error": float(record_delta.mean()),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
