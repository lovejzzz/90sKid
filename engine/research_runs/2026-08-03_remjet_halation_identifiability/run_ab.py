#!/usr/bin/env python3
"""Controlled V23 rem-jet halation identifiability test on original RAW frames.

The production baseline uses the existing two-Gaussian optical-scatter term.
The candidate removes only that term.  Neither state is claimed to be a measured
5279 point-spread function; the test asks whether the current empirical term has
an observable, independently defensible advantage on the available material.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
EXPERIMENT = ROOT / "experiments" / "emulsion_reconstruction"
sys.path.insert(0, str(EXPERIMENT / "src"))
import emulsion_experiment as e  # noqa: E402


OUT = Path(__file__).resolve().parent
DECODER = Path("/tmp/prores_raw_float_decode")
SOURCE_WIDTH, SOURCE_HEIGHT = 5760, 4320
TEST_WIDTH, TEST_HEIGHT = 1440, 1080
EXPOSURE_STOPS = 0.45
SAMPLES = [
    ("T002", Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV"), 97),
    ("T020", Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"), 12),
    ("T032", Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T032.MOV"), 12),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decode(path: Path, frame: int) -> np.ndarray:
    expected = SOURCE_WIDTH * SOURCE_HEIGHT * 3 * 4
    result = subprocess.run(
        [str(DECODER), str(path), str(frame), "1"],
        stdout=subprocess.PIPE,
        check=True,
    )
    if len(result.stdout) != expected:
        raise RuntimeError(f"decoder returned {len(result.stdout)} bytes, expected {expected}")
    raw = np.frombuffer(result.stdout, dtype="<f4").reshape(SOURCE_HEIGHT, SOURCE_WIDTH, 3)
    return cv2.resize(raw, (TEST_WIDTH, TEST_HEIGHT), interpolation=cv2.INTER_AREA)


def film_and_scatter_metrics(raw: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    common = dict(
        exposure_stops=EXPOSURE_STOPS,
        raw_colour="panasonic_official",
        sensor_noise_treatment="photochemical",
    )
    no_scatter = e.scene_to_5279_film_rgb(raw, include_optical_scatter=False, **common)
    current = e.scene_to_5279_film_rgb(raw, include_optical_scatter=True, **common)
    delta = current - no_scatter
    base_luma = np.einsum("...c,c->...", np.clip(no_scatter, 0.0, None), [0.2126, 0.7152, 0.0722])
    source = e.smoothstep(0.90, 3.5, base_luma)
    return current, no_scatter, {
        "pre_emulsion_luma_percentiles": np.percentile(base_luma, [50, 95, 99, 99.9, 100]).tolist(),
        "halation_source_nonzero_percent": float(100.0 * np.mean(source > 0.0)),
        "halation_source_above_half_percent": float(100.0 * np.mean(source > 0.5)),
        "added_scene_linear_rgb_mean": np.mean(delta, axis=(0, 1)).astype(float).tolist(),
        "added_scene_linear_rgb_max": np.max(delta, axis=(0, 1)).astype(float).tolist(),
        "added_scene_linear_luma_mean": float(np.mean(np.einsum("...c,c->...", delta, [0.2126, 0.7152, 0.0722]))),
    }


def controlled_density_pairs(
    current_film: np.ndarray,
    no_scatter_film: np.ndarray,
    frame: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Hold one developed dye-cloud deviation field fixed across the A/B.

    Calling NumPy's binomial sampler twice with slightly different probability
    arrays does not guarantee common random numbers: data-dependent sampling can
    advance the generator differently and decorrelate later layers.  Instead we
    form the production realization once and transplant its zero-mean density
    deviation onto the no-scatter mean.  Grain therefore remains in both images
    while the A/B isolates the deterministic optical-scatter exposure term.
    """
    current_records = e.film_records_from_rgb(current_film)
    candidate_records = e.film_records_from_rgb(no_scatter_film)
    current_mean = e.develop_5279_record_density(current_records)
    candidate_mean = e.develop_5279_record_density(candidate_records)
    current_formed = e.form_5279_multilayer_record_density(current_records, frame, 1.0, 1)
    density_deviation = current_formed - current_mean
    upper = e.SENSITO_DENSITY_RGB[:, -1] + 0.12
    candidate_formed = np.minimum(np.maximum(candidate_mean + density_deviation, 0.0), upper)
    return current_mean, current_formed, candidate_mean, candidate_formed.astype(np.float32)


def render_pair(
    densities: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    frame: int,
    look: str,
) -> tuple[np.ndarray, np.ndarray]:
    current_mean, current_formed, candidate_mean, candidate_formed = densities
    current = e.reconstruct_density_pair_to_display(current_mean, current_formed, frame, 1.0, look)
    candidate = e.reconstruct_density_pair_to_display(candidate_mean, candidate_formed, frame, 1.0, look)
    return current, candidate


def to_srgb_u8(bt709: np.ndarray) -> np.ndarray:
    srgb = e.srgb_encode(e.bt709_decode(bt709))
    return np.rint(np.clip(srgb, 0.0, 1.0) * 255.0).astype(np.uint8)


def save_rgb(path: Path, image: np.ndarray) -> None:
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def compare(stem: str, current: np.ndarray, no_scatter: np.ndarray) -> dict[str, float]:
    current_linear = e.bt709_decode(current)
    candidate_linear = e.bt709_decode(no_scatter)
    delta = candidate_linear - current_linear
    current_luma = np.einsum("...c,c->...", current_linear, [0.2126, 0.7152, 0.0722])
    candidate_luma = np.einsum("...c,c->...", candidate_linear, [0.2126, 0.7152, 0.0722])
    lab_current = e.linear_rec709_to_oklab(np.clip(current_linear, 0.0, None))
    lab_candidate = e.linear_rec709_to_oklab(np.clip(candidate_linear, 0.0, None))
    delta_e = np.linalg.norm(lab_candidate - lab_current, axis=-1)
    current_u8 = to_srgb_u8(current)
    candidate_u8 = to_srgb_u8(no_scatter)
    save_rgb(OUT / f"current_{stem}.png", current_u8)
    save_rgb(OUT / f"no_scatter_{stem}.png", candidate_u8)
    save_rgb(OUT / f"ab_current_vs_no_scatter_{stem}.png", np.concatenate([current_u8, candidate_u8], axis=1))
    amplified = np.clip(0.5 + 24.0 * delta, 0.0, 1.0)
    save_rgb(OUT / f"difference_x24_{stem}.png", np.rint(amplified * 255.0).astype(np.uint8))
    mse = float(np.mean(np.square(delta)))
    return {
        "linear_rgb_mae": float(np.mean(np.abs(delta))),
        "linear_rgb_max_abs": float(np.max(np.abs(delta))),
        "psnr_db": float("inf") if mse == 0.0 else float(-10.0 * np.log10(mse)),
        "oklab_delta_e_median": float(np.median(delta_e)),
        "oklab_delta_e_p95": float(np.percentile(delta_e, 95)),
        "oklab_delta_e_p99": float(np.percentile(delta_e, 99)),
        "absolute_luma_delta_p95": float(np.percentile(np.abs(candidate_luma - current_luma), 95)),
        "current_luma_p99": float(np.percentile(current_luma, 99)),
        "candidate_luma_p99": float(np.percentile(candidate_luma, 99)),
        "current_luma_max": float(np.max(current_luma)),
        "candidate_luma_max": float(np.max(candidate_luma)),
        "current_exact_black_percent": float(100.0 * np.mean(np.all(current_u8 == 0, axis=-1))),
        "candidate_exact_black_percent": float(100.0 * np.mean(np.all(candidate_u8 == 0, axis=-1))),
        "current_any_clipped_percent": float(100.0 * np.mean(np.any(current_linear >= 1.0, axis=-1))),
        "candidate_any_clipped_percent": float(100.0 * np.mean(np.any(candidate_linear >= 1.0, axis=-1))),
        "eight_bit_pixels_changed_percent": float(100.0 * np.mean(np.any(current_u8 != candidate_u8, axis=-1))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", nargs="*", choices=[item[0] for item in SAMPLES])
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    pixel_pitch_um = 24_900.0 / SOURCE_WIDTH
    report: dict[str, object] = {
        "question": "Is V23's inherited two-Gaussian red rem-jet halation term identifiable from public 5279 evidence and visibly preferable on the available RAW highlight boundaries?",
        "baseline": "V23 current optical scatter enabled",
        "candidate": "same V23 pipeline with only add_5279_optical_scatter disabled",
        "input_decode": "AVFoundation Apple extended-linear BT.2020 float32 from original 12-bit ProRes RAW HQ",
        "test_dimensions": [TEST_WIDTH, TEST_HEIGHT],
        "exposure_stops": EXPOSURE_STOPS,
        "current_empirical_kernel": {
            "near_sigma_pixels_at_5760": 5.5,
            "far_sigma_pixels_at_5760": 18.0,
            "near_sigma_micrometres_on_24p9mm_image": 5.5 * pixel_pitch_um,
            "far_sigma_micrometres_on_24p9mm_image": 18.0 * pixel_pitch_um,
            "near_weight": 0.035,
            "far_weight": 0.014,
            "scatter_rgb": [1.0, 0.22, 0.045],
            "source_smoothstep_scene_linear_luma": [0.90, 3.5],
            "evidence_status": "empirical V6 carry-over; public 5279 sheet confirms rem-jet but publishes no halo PSF, amplitude or spectral colour",
        },
        "controlled_variables": "Decode, Panasonic colour transform, exposure, sensor-noise treatment, H-D curves, one fixed developed dye-cloud density-deviation field, DIR, MTF, print/scan observers, finishing and output conversion are identical. Only pre-emulsion optical scatter is toggled.",
        "common_random_number_note": "The baseline finite-site realization is formed once. Its developed density deviation from the current mean is added to the no-scatter mean, avoiding NumPy binomial stream divergence when probability arrays differ.",
        "samples": {},
    }
    metrics_path = OUT / "metrics.json"
    if metrics_path.exists() and not args.fresh:
        prior = json.loads(metrics_path.read_text(encoding="utf-8"))
        report["samples"] = prior.get("samples", {})
    for name, path, frame in SAMPLES:
        if args.samples is not None and name not in args.samples:
            continue
        raw = decode(path, frame)
        current_film, no_scatter_film, scatter = film_and_scatter_metrics(raw)
        density_pairs = controlled_density_pairs(current_film, no_scatter_film, frame)
        sample: dict[str, object] = {
            "source": str(path),
            "source_sha256": sha256(path),
            "frame": frame,
            "scatter_activation": scatter,
            "branches": {},
        }
        for look, branch in (("2383_projection_monitor", "projection"), ("cineon_bluray", "scan")):
            current, candidate = render_pair(density_pairs, frame, look)
            sample["branches"][branch] = compare(f"{name.lower()}_{branch}", current, candidate)
        report["samples"][name] = sample
        # Preserve each completed original-RAW sample if a later decoder or
        # memory failure interrupts the remaining controlled test.
        metrics_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metrics_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
