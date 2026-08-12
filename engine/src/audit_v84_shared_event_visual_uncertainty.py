#!/usr/bin/env python3
"""Render exact shared-site uncertainty endpoints through both V72 observers.

This is deliberately a crop-scale research witness, not a new film profile.
Every alpha uses the same counter sequence: increasing alpha switches a matched
site from its independent uniforms to one common uniform.  The comparison is
therefore paired while every record retains its exact spatial Bernoulli p.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import cv2
import numpy as np

from audit_v79_projection_grain_policy_ownership import (
    luma_opponent_rms,
    mean_relative_tail_or_none,
)
from audit_v83_shared_event_dir_closure import allocate_class_counts
from emulsion5279 import legacy
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import ProResRawDecoder
from emulsion5279.pipeline import Emulsion5279Engine, FormedNegative


ALPHAS = (0.0, 0.25, 0.50, 1.0)
CROP_SIZE = 576
FRAME_WIDTH_MM = 24.9
LUMA = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float64)
FREQUENCY_BANDS_LP_MM = ((0.0, 8.0), (8.0, 16.0), (16.0, 32.0),
                         (32.0, 64.0), (64.0, 116.0))


def exact_integer_area(image: np.ndarray, factor: int) -> np.ndarray:
    height = image.shape[0] // factor * factor
    width = image.shape[1] // factor * factor
    trimmed = np.asarray(image[:height, :width], dtype=np.float64)
    return trimmed.reshape(
        height // factor, factor, width // factor, factor, image.shape[-1]
    ).mean(axis=(1, 3)).astype(np.float32)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def class_specifications(model) -> list[list[list[dict[str, object]]]]:
    site_counts = np.maximum(
        1,
        np.rint(model.SUBEMULSION_SITE_COUNT_PX_5760_RGB).astype(np.int32),
    )
    radii = (
        np.asarray(model.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB, dtype=np.float64)
        * float(model.NEGATIVE_GRAIN_CORRELATION_SCALE)
    )
    sigmas = np.asarray(
        model.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB, dtype=np.float64
    )
    result: list[list[list[dict[str, object]]]] = [
        [[], [], []], [[], [], []], [[], [], []]
    ]
    for record in range(3):
        for population in range(3):
            fractions = (
                np.asarray(model.GRAIN_SIZE_CLASS_FRACTIONS, dtype=np.float64)
                if model.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION is None
                else np.asarray(
                    model.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION[population],
                    dtype=np.float64,
                )
            )
            total = int(site_counts[record, population])
            counts = allocate_class_counts(total, fractions)
            for size_class, count in enumerate(counts):
                identity = record * 15 + population * 5 + size_class
                angle = 2.0 * math.pi * (
                    (identity + 0.5) * float(model.GRAIN_STABLE_PHASE_STEP) % 1.0
                ) + float(model.GRAIN_STABLE_PHASE_OFFSET_RADIANS)
                phase_radius = float(model.GRAIN_SUBPIXEL_PHASE_RADIUS_PX)
                radius = float(
                    radii[record, population]
                    * model.GRAIN_SIZE_CLASS_RADIUS_FACTORS[size_class]
                )
                sigma = float(
                    sigmas[record, population]
                    * model.GRAIN_SIZE_CLASS_OPTICAL_FACTORS[size_class]
                )
                kernel = model.disk_kernel(radius)
                kernel /= float(np.sum(kernel))
                result[record][population].append(
                    {
                        "count": int(count),
                        "weight": float(count) / total,
                        "radius": radius,
                        "sigma": sigma,
                        "offset": (
                            phase_radius * math.cos(angle),
                            phase_radius * math.sin(angle),
                        ),
                        "kernel": kernel,
                    }
                )
    return result


def sample_joint_class_fractions(
    probability_rgb: np.ndarray,
    site_counts_rgb: np.ndarray,
    alpha: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Exact spatial common-alpha mixture with a paired random sequence."""
    height, width = probability_rgb.shape[:2]
    site_counts_rgb = np.asarray(site_counts_rgb, dtype=np.int32)
    matched = int(np.min(site_counts_rgb))
    counts = np.zeros((height, width, 3), dtype=np.int16)
    for _ in range(matched):
        selector = rng.random((height, width), dtype=np.float32)
        common = rng.random((height, width), dtype=np.float32)
        use_common = selector < alpha
        for record in range(3):
            independent = rng.random((height, width), dtype=np.float32)
            active = np.where(
                use_common,
                common < probability_rgb[..., record],
                independent < probability_rgb[..., record],
            )
            counts[..., record] += active.astype(np.int16)
    for record in range(3):
        extra = int(site_counts_rgb[record] - matched)
        if extra:
            counts[..., record] += rng.binomial(
                extra, probability_rgb[..., record]
            ).astype(np.int16)
    return counts.astype(np.float32) / site_counts_rgb[None, None, :]


def form_shared_negative_crop(
    model,
    mean_density: np.ndarray,
    log_exposure: np.ndarray,
    activations: np.ndarray,
    alpha: float,
    seed: int,
    specs: list[list[list[dict[str, object]]]],
) -> tuple[FormedNegative, dict[str, object]]:
    started = time.perf_counter()
    shape = mean_density.shape[:2]
    rng = np.random.default_rng(seed)
    layers = np.zeros(shape + (3, 3), dtype=np.float32)
    aperture_radius = (
        0.5
        * float(model.KODAK_GRANULARITY_APERTURE_DIAMETER_UM)
        * 1e-3
        * (5760.0 / FRAME_WIDTH_MM)
    )
    population_power = np.zeros((3, 3), dtype=np.float64)

    for population in range(3):
        for size_class in range(5):
            class_counts = np.asarray(
                [specs[record][population][size_class]["count"] for record in range(3)],
                dtype=np.int32,
            )
            developed = sample_joint_class_fractions(
                activations[..., :, population],
                class_counts,
                alpha,
                rng,
            )
            for record in range(3):
                spec = specs[record][population][size_class]
                sampled = cv2.filter2D(
                    developed[..., record],
                    -1,
                    spec["kernel"],
                    borderType=cv2.BORDER_REFLECT,
                )
                expected = cv2.filter2D(
                    activations[..., record, population],
                    -1,
                    spec["kernel"],
                    borderType=cv2.BORDER_REFLECT,
                )
                sampled = cv2.GaussianBlur(
                    sampled,
                    (0, 0),
                    max(float(spec["sigma"]), 0.05),
                    borderType=cv2.BORDER_REFLECT,
                )
                expected = cv2.GaussianBlur(
                    expected,
                    (0, 0),
                    max(float(spec["sigma"]), 0.05),
                    borderType=cv2.BORDER_REFLECT,
                )
                deviation = sampled - expected
                offset_x, offset_y = spec["offset"]
                transform = np.asarray(
                    [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
                    dtype=np.float32,
                )
                deviation = cv2.warpAffine(
                    deviation,
                    transform,
                    (shape[1], shape[0]),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT,
                )
                layers[..., record, population] += (
                    float(spec["weight"]) * deviation
                )
                population_power[record, population] += (
                    float(spec["weight"]) ** 2
                    * model.filtered_kernel_power(
                        float(spec["radius"]),
                        float(spec["sigma"]),
                        aperture_radius,
                        tuple(float(value) for value in spec["offset"]),
                    )
                    / int(spec["count"])
                )

    net_capacity = (
        np.asarray(model.SENSITO_DENSITY_RGB[:, -1], dtype=np.float32)
        - np.asarray(model.SENSITO_DMIN_RGB, dtype=np.float32)
    )
    capacities = (
        net_capacity[:, None]
        * np.asarray(model.SUBEMULSION_CAPACITY_FRACTIONS, dtype=np.float32)[None, :]
    )
    predicted_variance = np.zeros(shape + (3,), dtype=np.float32)
    for record in range(3):
        for population in range(3):
            p = activations[..., record, population]
            predicted_variance[..., record] += (
                capacities[record, population] ** 2
                * p
                * (1.0 - p)
                * population_power[record, population]
            )
    target_sigma = model.published_5279_granularity_sigma(log_exposure)
    production_calibration = target_sigma / np.sqrt(
        np.maximum(predicted_variance, 1e-12)
    )
    coupled = model.couple_5279_population_deviations(
        layers, activations, 1.0
    )
    combined = np.sum(coupled * capacities[None, None, ...], axis=-1)
    unbounded = mean_density + combined * production_calibration
    if model.GRAIN_LOCAL_DENSITY_BOUND_MODE == "nonnegative_microscopic_density":
        formed = np.maximum(unbounded, 0.0)
    elif model.GRAIN_LOCAL_DENSITY_BOUND_MODE == "legacy_macro_dmax_plus_0_12":
        upper = model.SENSITO_DENSITY_RGB[:, -1] + 0.12
        formed = np.minimum(np.maximum(unbounded, 0.0), upper)
    else:
        raise ValueError(model.GRAIN_LOCAL_DENSITY_BOUND_MODE)
    return FormedNegative(mean_density, formed.astype(np.float32)), {
        "seconds": time.perf_counter() - started,
        "alpha": alpha,
        "seed": seed,
        "minimum_unbounded_density_rgb": np.min(unbounded, axis=(0, 1)).tolist(),
        "below_zero_before_bound_count": int(np.sum(unbounded < 0.0)),
        "bound_changed_sample_count": int(np.sum(formed != unbounded)),
        "calibration_range_rgb": [
            [
                float(np.min(production_calibration[..., record])),
                float(np.max(production_calibration[..., record])),
            ]
            for record in range(3)
        ],
    }


def covariance_summary(samples: np.ndarray) -> dict[str, object]:
    values = np.asarray(samples, dtype=np.float64).reshape(-1, 3)
    values -= np.mean(values, axis=0, keepdims=True)
    covariance = values.T @ values / max(values.shape[0] - 1, 1)
    sigma = np.sqrt(np.maximum(np.diag(covariance), 1e-30))
    correlation = covariance / np.outer(sigma, sigma)
    return {
        "sigma_rgb": sigma.tolist(),
        "covariance": covariance.tolist(),
        "correlation": correlation.tolist(),
    }


def filter_48um_density(model, residual: np.ndarray) -> np.ndarray:
    radius = 0.5 * 48e-3 * (5760.0 / FRAME_WIDTH_MM)
    aperture = model.disk_kernel(radius)
    aperture /= float(np.sum(aperture))
    filtered = np.stack(
        [
            cv2.filter2D(
                residual[..., record],
                -1,
                aperture,
                borderType=cv2.BORDER_REFLECT,
            )
            for record in range(3)
        ],
        axis=-1,
    )
    return filtered[48:-48, 48:-48]


def band_power_summary(residual: np.ndarray) -> dict[str, object]:
    values = np.asarray(residual, dtype=np.float64)
    values -= np.mean(values, axis=(0, 1), keepdims=True)
    height, width = values.shape[:2]
    spectrum = np.fft.rfft2(values, axes=(0, 1))
    fy = np.fft.fftfreq(height)[:, None] * (5760.0 / FRAME_WIDTH_MM)
    fx = np.fft.rfftfreq(width)[None, :] * (5760.0 / FRAME_WIDTH_MM)
    radial = np.sqrt(fx * fx + fy * fy)
    luma_spectrum = np.einsum("...c,c->...", spectrum, LUMA)
    opponent_spectrum = spectrum - luma_spectrum[..., None]
    normalization = float((height * width) ** 2)
    one_sided_weights = np.ones((1, spectrum.shape[1]), dtype=np.float64)
    if spectrum.shape[1] > 1:
        one_sided_weights[:, 1:] = 2.0
        if width % 2 == 0:
            one_sided_weights[:, -1] = 1.0
    rows: list[dict[str, object]] = []
    for low, high in FREQUENCY_BANDS_LP_MM:
        mask = (radial >= low) & (radial < high)
        if low == 0.0:
            mask[0, 0] = False
        weights = np.broadcast_to(one_sided_weights, radial.shape)[mask]
        luma_power = float(
            np.sum(np.abs(luma_spectrum[mask]) ** 2 * weights) / normalization
        )
        opponent_power = float(
            np.sum(np.abs(opponent_spectrum[mask]) ** 2 * weights[:, None])
            / (normalization * 3.0)
        )
        rows.append(
            {
                "range_lp_mm": [low, high],
                "luma_rms": math.sqrt(max(luma_power, 0.0)),
                "opponent_rms": math.sqrt(max(opponent_power, 0.0)),
                "opponent_over_luma": math.sqrt(max(opponent_power, 0.0))
                / max(math.sqrt(max(luma_power, 0.0)), 1e-30),
            }
        )
    return {"bands": rows}


def observer_summary(
    physical: np.ndarray,
    mean: np.ndarray,
) -> dict[str, object]:
    residual = physical - mean
    integrated = exact_integer_area(physical, 3)
    integrated_mean = exact_integer_area(mean, 3)
    native_rms = luma_opponent_rms(residual)
    integrated_rms = luma_opponent_rms(integrated - integrated_mean)
    return {
        "native_grain_rms": native_rms,
        "exact_3x3_integrated_grain_rms": integrated_rms,
        "exact_3x3_retention": {
            name: float(integrated_rms[name] / max(native_rms[name], 1e-30))
            for name in ("rgb", "luma", "opponent")
        },
        "mean_relative_colour_tail": mean_relative_tail_or_none(physical, mean),
        "frequency_bands": band_power_summary(residual[48:-48, 48:-48]),
    }


def write_srgb_png(model, path: Path, linear: np.ndarray) -> None:
    encoded = model.srgb_encode(np.asarray(linear, dtype=np.float32))
    code = np.rint(np.clip(encoded, 0.0, 1.0) * 65535.0).astype(np.uint16)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), cv2.cvtColor(code, cv2.COLOR_RGB2BGR)):
        raise RuntimeError(f"failed to write {path}")


def difference_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    delta = np.asarray(candidate, dtype=np.float64) - np.asarray(reference, dtype=np.float64)
    return {
        "rms": float(np.sqrt(np.mean(delta * delta))),
        "maximum_absolute": float(np.max(np.abs(delta))),
        "mean_absolute": float(np.mean(np.abs(delta))),
    }


def measure(
    input_path: Path,
    decoder_path: Path,
    output_dir: Path,
    start_frame: int,
    crop_x: int | None,
    crop_y: int | None,
) -> dict[str, object]:
    config = EngineConfig(
        profile="v72",
        exposure_stops=0.45,
        grain_scale=1.0,
        oversample=1,
        mode=EngineMode.REFERENCE,
        opencv_threads=8,
        binomial_workers=8,
        numba_threads=8,
        array_workers=8,
        observer_branch_workers=1,
        research_baseline=True,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    model = legacy.model
    if model.GRAIN_CALIBRATION_DOMAIN != "post_coupling_residual":
        raise RuntimeError("V84 must reproduce active V72 calibration")
    if model.GRAIN_SUBPIXEL_PHASE_MODE != "stable_balanced":
        raise RuntimeError("V84 requires V72 stable class phases")
    specs = class_specifications(model)
    try:
        decode_started = time.perf_counter()
        with ProResRawDecoder(
            decoder_path, input_path, start_frame, 1
        ) as decoder:
            absolute_frame, raw = next(iter(decoder))
        decode_seconds = time.perf_counter() - decode_started

        preparation_started = time.perf_counter()
        film_rgb = model.scene_to_5279_film_rgb(
            raw,
            exposure_stops=config.exposure_stops,
            raw_colour=engine.profile.PROFILE["raw_colour"],
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = model.film_records_from_rgb(film_rgb)
        log_exposure = np.log10(np.maximum(records, 1e-8)) - 1.0
        activations = model.subemulsion_activation_probabilities(log_exposure)
        mean = model.develop_5279_record_density_from_log_exposure(
            log_exposure, precomputed_activations=activations
        )
        preparation_seconds = time.perf_counter() - preparation_started
        height, width = mean.shape[:2]
        x0 = (width - CROP_SIZE) // 2 if crop_x is None else crop_x
        y0 = (height - CROP_SIZE) // 2 if crop_y is None else crop_y
        if not (0 <= x0 <= width - CROP_SIZE and 0 <= y0 <= height - CROP_SIZE):
            raise ValueError("crop lies outside decoded frame")
        crop = np.s_[y0 : y0 + CROP_SIZE, x0 : x0 + CROP_SIZE]
        mean_crop = np.ascontiguousarray(mean[crop], dtype=np.float32)
        log_crop = np.ascontiguousarray(log_exposure[crop], dtype=np.float32)
        activation_crop = np.ascontiguousarray(activations[crop], dtype=np.float32)

        endpoint_arrays: dict[str, dict[str, np.ndarray]] = {}
        endpoint_rows: dict[str, object] = {}
        for alpha in ALPHAS:
            negative, formation = form_shared_negative_crop(
                model,
                mean_crop,
                log_crop,
                activation_crop,
                alpha,
                840_000 + int(absolute_frame),
                specs,
            )
            observed_started = time.perf_counter()
            physical, deterministic = engine.observe_with_mean(
                negative, int(absolute_frame)
            )
            observer_seconds = time.perf_counter() - observed_started
            key = f"alpha_{alpha:.2f}"
            endpoint_arrays[key] = {
                "projection": physical.projection_linear_rec709,
                "scan": physical.scan_linear_rec709,
                "mean_projection": deterministic.projection_linear_rec709,
                "mean_scan": deterministic.scan_linear_rec709,
            }
            density_residual = (
                negative.formed_record_density - negative.mean_record_density
            )
            density_48 = filter_48um_density(model, density_residual)
            endpoint_rows[key] = {
                "alpha": alpha,
                "formation": formation,
                "observer_seconds": observer_seconds,
                "density_48um": covariance_summary(density_48),
                "density_native": covariance_summary(density_residual[48:-48, 48:-48]),
                "projection": observer_summary(
                    physical.projection_linear_rec709,
                    deterministic.projection_linear_rec709,
                ),
                "scan": observer_summary(
                    physical.scan_linear_rec709,
                    deterministic.scan_linear_rec709,
                ),
            }
            write_srgb_png(
                model,
                output_dir / key / "projection_srgb16.png",
                physical.projection_linear_rec709,
            )
            write_srgb_png(
                model,
                output_dir / key / "scan_srgb16.png",
                physical.scan_linear_rec709,
            )
        reference = endpoint_arrays["alpha_0.00"]
        for key, arrays in endpoint_arrays.items():
            for mean_branch in ("mean_projection", "mean_scan"):
                if not np.array_equal(reference[mean_branch], arrays[mean_branch]):
                    raise AssertionError(
                        "shared-event endpoint changed deterministic observer mean"
                    )
            endpoint_rows[key]["difference_from_alpha_0"] = {
                branch: difference_metrics(reference[branch], arrays[branch])
                for branch in ("projection", "scan")
            }
        write_srgb_png(
            model,
            output_dir / "deterministic" / "projection_srgb16.png",
            reference["mean_projection"],
        )
        write_srgb_png(
            model,
            output_dir / "deterministic" / "scan_srgb16.png",
            reference["mean_scan"],
        )
    finally:
        engine.close()

    alpha_zero = endpoint_rows["alpha_0.00"]
    alpha_one = endpoint_rows["alpha_1.00"]
    transfer_summary = {
        branch: {
            "alpha_1_luma_rms_over_alpha_0": float(
                alpha_one[branch]["native_grain_rms"]["luma"]
                / alpha_zero[branch]["native_grain_rms"]["luma"]
            ),
            "alpha_1_opponent_rms_over_alpha_0": float(
                alpha_one[branch]["native_grain_rms"]["opponent"]
                / alpha_zero[branch]["native_grain_rms"]["opponent"]
            ),
            "alpha_1_total_rgb_rms_over_alpha_0": float(
                alpha_one[branch]["native_grain_rms"]["rgb"]
                / alpha_zero[branch]["native_grain_rms"]["rgb"]
            ),
        }
        for branch in ("projection", "scan")
    }
    return {
        "audit": "V84 shared finite-event visual uncertainty endpoints",
        "profile": "V72 observers; experimental exact CPU negative sampler",
        "image_release": False,
        "input": {
            "path": str(input_path),
            "sha256": sha256(input_path),
            "absolute_frame": int(absolute_frame),
            "decoded_dimensions": [width, height],
            "crop_xywh": [x0, y0, CROP_SIZE, CROP_SIZE],
        },
        "paired_sampler": {
            "alphas": list(ALPHAS),
            "seed": 840_000 + int(absolute_frame),
            "law": (
                "Every matched site always draws selector, common U and three "
                "independent U values. Alpha changes only selector < alpha, so "
                "all endpoints are paired and each record remains Bernoulli(p)."
            ),
            "physical_site_alignment_is_measured": False,
        },
        "timing_seconds": {
            "decode": decode_seconds,
            "deterministic_full_frame_preparation": preparation_seconds,
        },
        "endpoints": endpoint_rows,
        "observer_energy_transfer_summary": transfer_summary,
        "artifacts": {
            "directory": str(output_dir),
            "encoding": "16-bit PNG, Rec.709 primaries, sRGB transfer",
            "authority": "research crop from one decoded RAW frame",
        },
        "decision": (
            "Do not promote a shared-site alpha. The experiment proves that alpha "
            "can trade opponent power for luma power while preserving each record's "
            "48 um marginal RMS, but it changes total visible grain energy and the "
            "two observers differently. Alpha=1 is rejected as a default extreme; "
            "alpha=.25/.50 remain diagnostic witnesses only. Re-audit the large "
            "blue-record marginal and the mapping from analytical record RMS to "
            "visible colour before using site sharing as a cure for electronic-looking grain."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("decoder", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--crop-x", type=int)
    parser.add_argument("--crop-y", type=int)
    args = parser.parse_args()
    report = measure(
        args.input,
        args.decoder,
        args.output_dir,
        args.start_frame,
        args.crop_x,
        args.crop_y,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["timing_seconds"], indent=2))
    for key, endpoint in report["endpoints"].items():
        print(key, endpoint["density_48um"]["correlation"])


if __name__ == "__main__":
    main()
