#!/usr/bin/env python3
"""V24 35 mm texture candidate study.

The published 48 um RMS curves constrain amplitude, but not the complete
spatial spectrum or the covariance seen after projection/scanning.  This test
keeps the mean negative and colour transforms fixed while comparing plausible
fine-grain spectra and restrained opponent-colour integration.
"""

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
OUT = HERE / "candidates"


PROFILES = {
    "v23": {},
    "fine35": {
        "correlation_scale": 0.76,
        "fractions": [0.16, 0.30, 0.32, 0.17, 0.05],
        "radius": [0.50, 0.68, 0.86, 1.08, 1.34],
        "optical": [0.68, 0.80, 0.92, 1.05, 1.18],
    },
    "fine35_integrated": {
        "correlation_scale": 0.76,
        "fractions": [0.16, 0.30, 0.32, 0.17, 0.05],
        "radius": [0.50, 0.68, 0.86, 1.08, 1.34],
        "optical": [0.68, 0.80, 0.92, 1.05, 1.18],
        "projection_chroma_sigma": 0.62,
        "projection_chroma_hf": 0.36,
        "projection_chroma_strength": 0.66,
        "scan_chroma_sigma": 0.72,
        "scan_chroma_hf": 0.30,
        "scan_chroma_strength": 0.64,
    },
    "fine35_quiet": {
        "correlation_scale": 0.70,
        "fractions": [0.20, 0.32, 0.30, 0.14, 0.04],
        "radius": [0.45, 0.60, 0.78, 1.00, 1.28],
        "optical": [0.62, 0.74, 0.88, 1.02, 1.16],
        "projection_chroma_sigma": 0.68,
        "projection_chroma_hf": 0.28,
        "projection_chroma_strength": 0.60,
        "scan_chroma_sigma": 0.78,
        "scan_chroma_hf": 0.24,
        "scan_chroma_strength": 0.58,
    },
}


def load(name: str, profile: dict[str, object]):
    spec = importlib.util.spec_from_file_location(name, SRC)
    if spec is None or spec.loader is None:
        raise RuntimeError(SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if profile:
        module.NEGATIVE_GRAIN_CORRELATION_SCALE = profile["correlation_scale"]
        module.GRAIN_SIZE_CLASS_FRACTIONS = np.asarray(profile["fractions"], np.float32)
        module.GRAIN_SIZE_CLASS_RADIUS_FACTORS = np.asarray(profile["radius"], np.float32)
        module.GRAIN_SIZE_CLASS_OPTICAL_FACTORS = np.asarray(profile["optical"], np.float32)
        module.PROJECTION_CHROMA_GRAIN_SIGMA_AT_2K = profile.get("projection_chroma_sigma", 0.0)
        module.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION = profile.get("projection_chroma_hf", 1.0)
        module.PROJECTION_CHROMA_GRAIN_OPPONENT_STRENGTH = profile.get("projection_chroma_strength", 1.0)
        module.BLURAY_CHROMA_GRAIN_SIGMA_AT_2K = profile.get("scan_chroma_sigma", 0.55)
        module.BLURAY_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION = profile.get("scan_chroma_hf", 0.55)
        module.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH = profile.get("scan_chroma_strength", 1.0)
    return module


MODELS = {name: load(f"v24_{name}", profile) for name, profile in PROFILES.items()}
BASE = MODELS["v23"]


def aperture_sigma(e, deviation: np.ndarray, width: int) -> np.ndarray:
    radius = 0.5 * e.KODAK_GRANULARITY_APERTURE_DIAMETER_UM * 1e-3 * width / 24.9
    kernel = e.disk_kernel(radius)
    kernel /= kernel.sum()
    measured = np.stack(
        [cv2.filter2D(deviation[..., c], -1, kernel, borderType=cv2.BORDER_REFLECT) for c in range(3)],
        axis=-1,
    )
    margin = max(8, int(np.ceil(radius * 3)))
    return np.std(measured[margin:-margin, margin:-margin], axis=(0, 1))


def nps_bands(field: np.ndarray) -> dict[str, float]:
    h, w = field.shape
    size = min(256, h, w)
    patch = field[(h-size)//2:(h+size)//2, (w-size)//2:(w+size)//2]
    patch = patch - np.mean(patch)
    window = np.outer(np.hanning(size), np.hanning(size))
    power = np.abs(np.fft.fftshift(np.fft.fft2(patch * window))) ** 2
    fy, fx = np.meshgrid(np.fft.fftshift(np.fft.fftfreq(size)), np.fft.fftshift(np.fft.fftfreq(size)), indexing="ij")
    radius = np.sqrt(fx * fx + fy * fy)

    def band(a: float, b: float) -> float:
        return float(np.mean(power[(radius >= a) & (radius < b)]))

    low, mid, high = band(0.015, 0.075), band(0.075, 0.20), band(0.25, 0.42)
    return {"low_mid": low / mid, "high_mid": high / mid}


def grain_metrics(mean: np.ndarray, stochastic: np.ndarray) -> dict[str, object]:
    delta = stochastic - mean
    luma = np.einsum("...c,c->...", delta, [0.2126, 0.7152, 0.0722])
    opponent = delta - luma[..., None]
    return {
        "mean_drift_rgb": np.mean(delta, axis=(0, 1)).tolist(),
        "rms_rgb": np.std(delta, axis=(0, 1)).tolist(),
        "luma_rms": float(np.std(luma)),
        "opponent_rms": float(np.sqrt(np.mean(opponent * opponent))),
        "opponent_to_luma_rms": float(np.sqrt(np.mean(opponent * opponent)) / max(np.std(luma), 1e-9)),
        "luma_nps": nps_bands(luma),
        "correlation_rgb": np.corrcoef(delta.reshape(-1, 3), rowvar=False).tolist(),
    }


def uniform_tests() -> dict[str, object]:
    height, width = 256, 1440
    report: dict[str, object] = {}
    for loge in (-3.0, -2.0, -1.0):
        records = np.full((height, width, 3), 10.0 ** (loge + 1.0), np.float32)
        target = BASE.published_5279_granularity_sigma(np.full((1, 1, 3), loge, np.float32))[0, 0]
        row: dict[str, object] = {"target_sigma_d": target.tolist()}
        for name, model in MODELS.items():
            mean = model.develop_5279_record_density(records)
            measured = []
            first = None
            elapsed = []
            for frame in (0, 1):
                mark = time.perf_counter()
                formed = model.form_5279_multilayer_record_density(records, frame, 1.0, 1)
                elapsed.append(time.perf_counter() - mark)
                deviation = formed - mean
                measured.append(aperture_sigma(model, deviation, width))
                if first is None:
                    first = deviation
            sigma = np.mean(measured, axis=0)
            row[name] = {
                "measured_sigma_d": sigma.tolist(),
                "maximum_absolute_relative_error": float(np.max(np.abs(sigma / target - 1.0))),
                "formation_seconds": float(np.mean(elapsed)),
                "nps_rgb": {str(c): nps_bands(first[..., c]) for c in range(3)},
            }
        report[str(loge)] = row
    return report


def decode(path: Path, frame: int) -> np.ndarray:
    width, height, _ = BASE.probe_video(path)
    result = subprocess.run([str(DECODER), str(path), str(frame), "1"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(height, width, 3)
    return cv2.resize(raw, (1440, 1080), interpolation=cv2.INTER_AREA).astype(np.float32)


def save(path: Path, image: np.ndarray) -> None:
    srgb = BASE.srgb_encode(BASE.bt709_decode(np.clip(image, 0.0, 1.0)))
    u8 = np.rint(srgb * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(u8, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 97])


def real_frame_tests() -> dict[str, object]:
    report: dict[str, object] = {}
    for source in SOURCES:
        clip, frame = source.stem.split("_")[-1].lower(), 12
        raw = decode(source, frame)
        film = BASE.scene_to_5279_film_rgb(raw, exposure_stops=0.45, raw_colour="panasonic_official", include_optical_scatter=True, sensor_noise_treatment="photochemical")
        records = BASE.film_records_from_rgb(film)
        mean_density = BASE.develop_5279_record_density(records)
        row: dict[str, object] = {}
        projection_strip, scan_strip = [], []
        reference_means: dict[str, np.ndarray] = {}
        for name, model in MODELS.items():
            mark = time.perf_counter()
            formed = model.form_5279_multilayer_record_density(records, frame, 1.0, 1)
            formation_seconds = time.perf_counter() - mark
            projection_mean = model.reconstruct_density_pair_to_display(mean_density, mean_density, frame, 1.0, "2383_projection_monitor")
            projection = model.reconstruct_density_pair_to_display(mean_density, formed, frame, 1.0, "2383_projection_monitor")
            scan_mean = model.reconstruct_density_pair_to_display(mean_density, mean_density, frame, 1.0, "cineon_bluray")
            scan = model.reconstruct_density_pair_to_display(mean_density, formed, frame, 1.0, "cineon_bluray")
            save(OUT / f"{clip}_{name}_projection.jpg", projection)
            save(OUT / f"{clip}_{name}_scan.jpg", scan)
            projection_strip.append(projection)
            scan_strip.append(scan)
            if name == "v23":
                reference_means = {"projection": projection_mean, "scan": scan_mean}
            row[name] = {
                "formation_seconds_1440": formation_seconds,
                "negative_grain": grain_metrics(mean_density, formed),
                "projection_grain": grain_metrics(projection_mean, projection),
                "scan_grain": grain_metrics(scan_mean, scan),
                "projection_mean_max_abs_change_from_v23": float(np.max(np.abs(projection_mean - reference_means.get("projection", projection_mean)))),
                "scan_mean_max_abs_change_from_v23": float(np.max(np.abs(scan_mean - reference_means.get("scan", scan_mean)))),
            }
        save(OUT / f"{clip}_projection_strip_v23_fine_integrated_quiet.jpg", np.concatenate(projection_strip, axis=1))
        save(OUT / f"{clip}_scan_strip_v23_fine_integrated_quiet.jpg", np.concatenate(scan_strip, axis=1))
        report[clip] = row
        del raw, film, records, mean_density
        gc.collect()
    return report


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = {
        "purpose": "choose a finer 35 mm-like NPS and colour-grain integration without changing mean colour/tone",
        "profiles": PROFILES,
        "uniform_48um_tests": uniform_tests(),
        "real_frames": real_frame_tests(),
    }
    (HERE / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
