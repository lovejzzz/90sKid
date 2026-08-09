#!/usr/bin/env python3
"""Validate V23 five-point dye-cloud quadrature against V22 and Kodak RMS."""

from __future__ import annotations

import gc
import importlib.util
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "src" / "emulsion_experiment.py"
DECODER = Path("/tmp/prores_raw_float_decode")
SOURCES = [
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"),
    Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T032.MOV"),
]
OUT = HERE / "grain_candidate"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SRC)
    if spec is None or spec.loader is None:
        raise RuntimeError(SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


baseline = load("v22_grain_baseline")
candidate = load("v23_grain_candidate")
baseline.NEGATIVE_GRAIN_CORRELATION_SCALE = 0.88
baseline.GRAIN_SIZE_CLASS_FRACTIONS = np.array([0.30, 0.53, 0.17], np.float32)
baseline.GRAIN_SIZE_CLASS_RADIUS_FACTORS = np.array([0.70, 1.00, 1.42], np.float32)
baseline.GRAIN_SIZE_CLASS_OPTICAL_FACTORS = np.array([0.82, 1.00, 1.20], np.float32)
baseline.GRAIN_SIZE_CLASS_PHASE_STEP_RADIANS = 2.0 * np.pi / 3.0


def aperture_sigma(e, deviation: np.ndarray, width: int) -> np.ndarray:
    radius = 0.5 * e.KODAK_GRANULARITY_APERTURE_DIAMETER_UM * 1e-3 * width / 24.9
    kernel = e.disk_kernel(radius)
    kernel /= kernel.sum()
    measured = np.stack(
        [cv2.filter2D(deviation[..., c], -1, kernel, borderType=cv2.BORDER_REFLECT) for c in range(3)],
        axis=-1,
    )
    margin = max(8, int(np.ceil(radius * 3)))
    crop = measured[margin:-margin, margin:-margin]
    return np.std(crop, axis=(0, 1))


def radial_nps_slope(field: np.ndarray) -> dict[str, float]:
    patch = field[:256, (field.shape[1] - 256) // 2:(field.shape[1] + 256) // 2]
    patch = patch - np.mean(patch)
    window = np.outer(np.hanning(256), np.hanning(256))
    power = np.abs(np.fft.fftshift(np.fft.fft2(patch * window))) ** 2
    fy, fx = np.meshgrid(np.fft.fftshift(np.fft.fftfreq(256)), np.fft.fftshift(np.fft.fftfreq(256)), indexing="ij")
    radius = np.sqrt(fx * fx + fy * fy)
    bins = np.linspace(0.008, 0.48, 80)
    centers = 0.5 * (bins[:-1] + bins[1:])
    radial = np.array([np.mean(power[(radius >= a) & (radius < b)]) for a, b in zip(bins[:-1], bins[1:])])
    valid = (centers >= 0.025) & (centers <= 0.35) & np.isfinite(radial) & (radial > 0)
    slope = np.polyfit(np.log(centers[valid]), np.log(radial[valid]), 1)[0]
    return {
        "log_power_slope_0p025_to_0p35_cyc_px": float(slope),
        "low_to_mid_power_ratio": float(np.mean(radial[(centers >= 0.025) & (centers < 0.08)]) / np.mean(radial[(centers >= 0.08) & (centers < 0.20)])),
        "high_to_mid_power_ratio": float(np.mean(radial[(centers >= 0.25) & (centers < 0.40)]) / np.mean(radial[(centers >= 0.08) & (centers < 0.20)])),
    }


def uniform_tests() -> dict[str, object]:
    height, width = 256, 1440
    report: dict[str, object] = {}
    for loge in (-3.0, -2.0, -1.0):
        records = np.full((height, width, 3), 10.0 ** (loge + 1.0), np.float32)
        target = candidate.published_5279_granularity_sigma(np.full((1, 1, 3), loge, np.float32))[0, 0]
        row: dict[str, object] = {"target_sigma_d": target.tolist()}
        for name, model in (("v22", baseline), ("v23", candidate)):
            mean = model.develop_5279_record_density(records)
            sigmas, means, times = [], [], []
            first_deviation = None
            for frame in range(3):
                start = time.perf_counter()
                formed = model.form_5279_multilayer_record_density(records, frame, 1.0, 1)
                times.append(time.perf_counter() - start)
                deviation = formed - mean
                sigmas.append(aperture_sigma(model, deviation, width))
                means.append(np.mean(deviation, axis=(0, 1)))
                if first_deviation is None:
                    first_deviation = deviation.copy()
            measured = np.mean(sigmas, axis=0)
            row[name] = {
                "measured_sigma_d": measured.tolist(),
                "absolute_relative_error": np.abs(measured / target - 1.0).tolist(),
                "maximum_absolute_relative_error": float(np.max(np.abs(measured / target - 1.0))),
                "maximum_temporal_mean_drift_d": float(np.max(np.abs(means))),
                "mean_formation_seconds": float(np.mean(times)),
                "nps": {f"record_{c}": radial_nps_slope(first_deviation[..., c]) for c in range(3)},
            }
        report[str(loge)] = row
    return report


def decode(path: Path, frame: int) -> np.ndarray:
    width, height, _ = candidate.probe_video(path)
    result = subprocess.run([str(DECODER), str(path), str(frame), "1"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(height, width, 3)
    return cv2.resize(raw, (1440, 1080), interpolation=cv2.INTER_AREA).astype(np.float32)


def save(path: Path, image: np.ndarray) -> None:
    srgb = candidate.srgb_encode(candidate.bt709_decode(np.clip(image, 0.0, 1.0)))
    u8 = np.rint(srgb * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(u8, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 96])


def real_frame_tests() -> dict[str, object]:
    report: dict[str, object] = {}
    for source in SOURCES:
        clip, frame = source.stem.split("_")[-1].lower(), 36
        raw = decode(source, frame)
        film = candidate.scene_to_5279_film_rgb(raw, exposure_stops=0.45, raw_colour="panasonic_official", include_optical_scatter=True, sensor_noise_treatment="photochemical")
        records = candidate.film_records_from_rgb(film)
        mean = candidate.develop_5279_record_density(records)
        row: dict[str, object] = {}
        images = []
        for name, model in (("v22", baseline), ("v23", candidate)):
            start = time.perf_counter()
            formed = model.form_5279_multilayer_record_density(records, frame, 1.0, 1)
            formation_time = time.perf_counter() - start
            projection = model.reconstruct_density_pair_to_display(mean, formed, frame, 1.0, "2383_projection_monitor")
            scan = model.reconstruct_density_pair_to_display(mean, formed, frame, 1.0, "cineon_bluray")
            save(OUT / f"{clip}_{name}_projection.jpg", projection)
            save(OUT / f"{clip}_{name}_scan.jpg", scan)
            images.append(np.concatenate([projection, scan], axis=1))
            deviation = formed - mean
            row[name] = {
                "formation_seconds_1440": formation_time,
                "density_deviation_std_rgb": np.std(deviation, axis=(0, 1)).tolist(),
                "density_deviation_correlation": np.corrcoef(deviation.reshape(-1, 3), rowvar=False).tolist(),
                "maximum_abs_density_deviation": float(np.max(np.abs(deviation))),
            }
        comparison = np.concatenate(images, axis=0)
        save(OUT / f"{clip}_v22_v23_comparison.jpg", comparison)
        report[clip] = row
        del raw, film, records, mean, images
        gc.collect()
    return report


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = {
        "candidate": {
            "correlation_scale": candidate.NEGATIVE_GRAIN_CORRELATION_SCALE,
            "fractions": candidate.GRAIN_SIZE_CLASS_FRACTIONS.tolist(),
            "radius_factors": candidate.GRAIN_SIZE_CLASS_RADIUS_FACTORS.tolist(),
            "optical_factors": candidate.GRAIN_SIZE_CLASS_OPTICAL_FACTORS.tolist(),
            "phase_step_radians": candidate.GRAIN_SIZE_CLASS_PHASE_STEP_RADIANS,
        },
        "uniform_48um_tests": uniform_tests(),
        "real_frames": real_frame_tests(),
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
