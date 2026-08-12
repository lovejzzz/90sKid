#!/usr/bin/env python3
"""Locate catastrophic microscopic-density tails in one real V72 frame.

This audit keeps the accepted image model unchanged.  It records every finite-
site class operator, locates the final formed-density extrema, and evaluates the
post-process RMS calibration at those pixels.  Running it in separate processes
for Archive CPU and Production Metal distinguishes a model tail from a backend
write/corruption failure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from emulsion5279 import legacy
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import ProResRawDecoder
from emulsion5279.pipeline import Emulsion5279Engine


MODES = {
    "archive_cpu": EngineMode.ARCHIVE_EXACT_CPU,
    "production_metal": EngineMode.PRODUCTION_METAL,
}


def array_summary(values: np.ndarray) -> dict[str, object]:
    source = np.asarray(values, dtype=np.float64)
    return {
        "minimum_rgb": np.min(source, axis=(0, 1)).tolist(),
        "maximum_rgb": np.max(source, axis=(0, 1)).tolist(),
        "percentile_99_999_rgb": np.percentile(
            source.reshape(-1, 3), 99.999, axis=0
        ).tolist(),
        "nonfinite_count": int(np.count_nonzero(~np.isfinite(source))),
    }


def local_calibration(model, log_exposure: np.ndarray, width: int) -> dict[str, object]:
    exposure = np.asarray(log_exposure, dtype=np.float32).reshape(1, 1, 3)
    stochastic_exposure = exposure
    if (
        model.GRAIN_STOCHASTIC_EXPOSURE_POLICY
        == "full_stochastic_state_endpoint_hold"
    ):
        stochastic_exposure = np.clip(
            exposure,
            float(model.GRANULARITY_LOG_EXPOSURE[0]),
            float(model.GRANULARITY_LOG_EXPOSURE[-1]),
        )
    activations = model.subemulsion_activation_probabilities(
        stochastic_exposure
    )[0, 0]
    target = model.published_5279_granularity_sigma(exposure)[0, 0]
    work_scale = width / 5760.0
    aperture_radius = (
        0.5
        * model.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
        * 1e-3
        * (width / 24.9)
    )
    radii = (
        model.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB
        * work_scale
        * model.NEGATIVE_GRAIN_CORRELATION_SCALE
    )
    sigmas = model.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB * work_scale
    site_counts = np.maximum(
        1,
        np.rint(
            model.SUBEMULSION_SITE_COUNT_PX_5760_RGB
            / max(work_scale * work_scale, 1e-6)
        ).astype(np.int32),
    )
    net_capacity = model.SENSITO_DENSITY_RGB[:, -1] - model.SENSITO_DMIN_RGB
    capacities = net_capacity[:, None] * model.SUBEMULSION_CAPACITY_FRACTIONS[None, :]
    predicted = np.zeros(3, dtype=np.float64)
    for channel in range(3):
        for population in range(3):
            total_sites = int(site_counts[channel, population])
            fractions = (
                model.GRAIN_SIZE_CLASS_FRACTIONS
                if model.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION is None
                else model.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION[population]
            )
            raw_counts = fractions * total_sites
            counts = np.maximum(np.floor(raw_counts).astype(np.int32), 1)
            while int(np.sum(counts)) < total_sites:
                counts[int(np.argmax(raw_counts - counts))] += 1
            while int(np.sum(counts)) > total_sites:
                removable = np.where(counts > 1, counts, 0)
                counts[int(np.argmax(removable))] -= 1
            power = 0.0
            for size_class, class_sites in enumerate(counts):
                weight = float(class_sites) / float(total_sites)
                identity = channel * 15 + population * 5 + size_class
                angle = 2.0 * np.pi * (
                    (identity + 0.5) * model.GRAIN_STABLE_PHASE_STEP % 1.0
                ) + model.GRAIN_STABLE_PHASE_OFFSET_RADIANS
                phase_radius = model.GRAIN_SUBPIXEL_PHASE_RADIUS_PX * work_scale
                offset = (
                    phase_radius * np.cos(angle),
                    phase_radius * np.sin(angle),
                )
                radius = float(
                    radii[channel, population]
                    * model.GRAIN_SIZE_CLASS_RADIUS_FACTORS[size_class]
                )
                sigma = float(
                    sigmas[channel, population]
                    * model.GRAIN_SIZE_CLASS_OPTICAL_FACTORS[size_class]
                )
                power += (
                    weight
                    * weight
                    * model.filtered_kernel_power(
                        radius, sigma, aperture_radius, offset
                    )
                    / float(class_sites)
                )
            probability = float(activations[channel, population])
            predicted[channel] += (
                float(capacities[channel, population]) ** 2
                * probability
                * (1.0 - probability)
                * power
            )
    calibration = target.astype(np.float64) / np.sqrt(
        np.maximum(predicted, 1e-12)
    )
    return {
        "log_exposure_rgb": exposure[0, 0].tolist(),
        "stochastic_log_exposure_rgb": stochastic_exposure[0, 0].tolist(),
        "activation_probability_by_record_population": activations.tolist(),
        "target_48um_sigma_d_rgb": target.tolist(),
        "predicted_48um_variance_rgb": predicted.tolist(),
        "post_process_calibration_rgb": calibration.tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--mode", choices=tuple(MODES), required=True)
    parser.add_argument(
        "--stochastic-exposure-policy",
        choices=(
            "legacy_target_only_endpoint_hold",
            "full_stochastic_state_endpoint_hold",
        ),
        default="legacy_target_only_endpoint_hold",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = EngineConfig(
        profile="v72",
        mode=MODES[args.mode],
        observer_branch_workers=1,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    model = legacy.model
    model.GRAIN_STOCHASTIC_EXPOSURE_POLICY = args.stochastic_exposure_policy
    class_rows: list[dict[str, object]] = []
    reference_sampler = model.binomial_dye_cloud_deviation

    def audited_sampler(
        activation_probability,
        rng,
        radius,
        optical_sigma,
        site_count,
        subpixel_offset=(0.0, 0.0),
        sample_seed=None,
    ):
        deviation = reference_sampler(
            activation_probability,
            rng,
            radius,
            optical_sigma,
            site_count,
            subpixel_offset,
            sample_seed=sample_seed,
        )
        probability = np.asarray(activation_probability)
        finite = np.isfinite(deviation)
        class_rows.append(
            {
                "call": len(class_rows),
                "sample_seed": int(sample_seed),
                "site_count": int(site_count),
                "probability_minimum": float(np.min(probability)),
                "probability_maximum": float(np.max(probability)),
                "deviation_minimum": float(np.min(deviation)),
                "deviation_maximum": float(np.max(deviation)),
                "nonfinite_count": int(np.count_nonzero(~finite)),
            }
        )
        return deviation

    model.binomial_dye_cloud_deviation = audited_sampler
    try:
        with ProResRawDecoder(
            args.decoder, args.source, args.frame, 1
        ) as decoder:
            absolute_frame, raw = next(iter(decoder))
        started = time.perf_counter()
        negative = engine.form_negative(raw, absolute_frame)
        elapsed = time.perf_counter() - started
        formed = negative.formed_record_density
        mean = negative.mean_record_density
        flat = formed.reshape(-1, 3)
        worst_flat: list[int] = []
        for channel in range(3):
            worst_flat.extend(
                np.argpartition(flat[:, channel], -4)[-4:].tolist()
            )
        worst_flat = sorted(
            set(worst_flat), key=lambda index: float(np.max(flat[index])), reverse=True
        )[:8]

        # Recreate only the deterministic record exposure, then retain just the
        # handful of pixels needed to diagnose the stochastic tail.
        film_rgb = model.scene_to_5279_film_rgb(
            raw,
            exposure_stops=config.exposure_stops,
            raw_colour=engine.profile.PROFILE["raw_colour"],
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = model.film_records_from_rgb(film_rgb)
        worst_rows = []
        for flat_index in worst_flat:
            y, x = divmod(int(flat_index), formed.shape[1])
            log_exposure = np.log10(np.maximum(records[y, x], 1e-8)) - 1.0
            worst_rows.append(
                {
                    "pixel_xy": [x, y],
                    "formed_density_rgb": formed[y, x].tolist(),
                    "mean_density_rgb": mean[y, x].tolist(),
                    "local_calibration": local_calibration(
                        model, log_exposure, formed.shape[1]
                    ),
                }
            )

        dmin = np.asarray(model.SENSITO_DMIN_RGB, dtype=np.float32)
        capacity = (
            np.asarray(model.SENSITO_DENSITY_RGB[:, -1], dtype=np.float32) - dmin
        )
        microscopic_limit = dmin + 1.08 * capacity
        report = {
            "audit": "V46 real-frame microscopic density tail",
            "profile": "v72",
            "execution_mode": args.mode,
            "source": str(args.source),
            "absolute_frame": int(absolute_frame),
            "shape": list(formed.shape),
            "negative_formation_seconds": elapsed,
            "grain_calibration_domain": model.GRAIN_CALIBRATION_DOMAIN,
            "local_density_bound_mode": model.GRAIN_LOCAL_DENSITY_BOUND_MODE,
            "stochastic_exposure_policy": (
                model.GRAIN_STOCHASTIC_EXPOSURE_POLICY
            ),
            "mean_density": array_summary(mean),
            "formed_density": array_summary(formed),
            "comparison_microscopic_limit_rgb": microscopic_limit.tolist(),
            "formed_above_comparison_limit_count_rgb": np.sum(
                formed > microscopic_limit[None, None, :], axis=(0, 1)
            ).tolist(),
            "formed_at_zero_count_rgb": np.sum(formed == 0.0, axis=(0, 1)).tolist(),
            "worst_pixels": worst_rows,
            "finite_site_class_calls": class_rows,
            "finite_site_class_maximum_absolute_deviation": float(
                max(
                    max(abs(row["deviation_minimum"]), abs(row["deviation_maximum"]))
                    for row in class_rows
                )
            ),
        }
        if args.mode == "production_metal":
            report["production_sampler_audit"] = engine.validate_rendered_frames(1)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        model.binomial_dye_cloud_deviation = reference_sampler
        engine.close()


if __name__ == "__main__":
    main()
