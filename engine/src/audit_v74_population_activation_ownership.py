#!/usr/bin/env python3
"""Audit fast/medium/slow ownership of 5279 mean density and grain variance.

Kodak publishes the finished stock's neutral H-D, MTF and 48 um marginal RMS,
not a 5279 population recipe.  This audit expands the current three-logistic
prior analytically and records what the final RMS normalization does and does
not identify.  It changes no profile constants or image pixels.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v72_profile
from audit_v46_5279_aperture_rms import measure as measure_aperture_rms


RECORDS = ("red_cyan", "green_magenta", "blue_yellow")
POPULATIONS = ("fast", "medium", "slow")
DEFAULT_LOG_EXPOSURES = tuple(float(x) for x in np.arange(-4.0, 0.01, 0.5))
FILM_IMAGE_WIDTH_MM = 24.9
NATIVE_WIDTH_PX = 5760


def class_counts(total_sites: int, fractions: np.ndarray) -> np.ndarray:
    raw = fractions * total_sites
    counts = np.maximum(np.floor(raw).astype(np.int32), 1)
    while int(np.sum(counts)) < total_sites:
        counts[int(np.argmax(raw - counts))] += 1
    while int(np.sum(counts)) > total_sites:
        removable = np.where(counts > 1, counts, 0)
        counts[int(np.argmax(removable))] -= 1
    return counts


def population_kernel_powers(
    *,
    aperture_radius: float,
    site_count_scale: float = 1.0,
    correlation_scale: float | None = None,
    shared_class_fractions: np.ndarray | None = None,
    radius_factors: np.ndarray | None = None,
    optical_factors: np.ndarray | None = None,
) -> np.ndarray:
    result = np.zeros((3, 3), dtype=np.float64)
    radii = (
        e.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB
        * (
            e.NEGATIVE_GRAIN_CORRELATION_SCALE
            if correlation_scale is None
            else correlation_scale
        )
    )
    active_radius_factors = (
        e.GRAIN_SIZE_CLASS_RADIUS_FACTORS
        if radius_factors is None
        else radius_factors
    )
    active_optical_factors = (
        e.GRAIN_SIZE_CLASS_OPTICAL_FACTORS
        if optical_factors is None
        else optical_factors
    )
    for record in range(3):
        for population in range(3):
            total_sites = max(
                5,
                int(
                    np.rint(
                        e.SUBEMULSION_SITE_COUNT_PX_5760_RGB[record, population]
                        * site_count_scale
                    )
                ),
            )
            if shared_class_fractions is not None:
                fractions = shared_class_fractions
            else:
                fractions = (
                    e.GRAIN_SIZE_CLASS_FRACTIONS
                    if e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION is None
                    else e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION[population]
                )
            counts = class_counts(total_sites, fractions)
            for size_class, sites in enumerate(counts):
                weight = float(sites) / float(total_sites)
                radius = float(
                    radii[record, population]
                    * active_radius_factors[size_class]
                )
                sigma = float(
                    e.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB[record, population]
                    * active_optical_factors[size_class]
                )
                result[record, population] += (
                    weight
                    * weight
                    * e.filtered_kernel_power(
                        radius, sigma, aperture_radius, (0.0, 0.0)
                    )
                    / float(sites)
                )
    return result


def historical_morphology_ablation(
    log_exposures: tuple[float, ...],
    aperture_radius: float,
    current_pixel_power: np.ndarray,
    current_aperture_power: np.ndarray,
) -> dict[str, object]:
    v23 = {
        "correlation_scale": 0.86,
        "fractions": np.asarray([0.10, 0.24, 0.34, 0.22, 0.10]),
        "radius_factors": np.asarray([0.62, 0.78, 0.98, 1.22, 1.55]),
        "optical_factors": np.asarray([0.78, 0.88, 1.00, 1.12, 1.25]),
    }
    v23_pixel = population_kernel_powers(
        aperture_radius=0.0,
        correlation_scale=float(v23["correlation_scale"]),
        shared_class_fractions=v23["fractions"],
        radius_factors=v23["radius_factors"],
        optical_factors=v23["optical_factors"],
    )
    v23_aperture = population_kernel_powers(
        aperture_radius=aperture_radius,
        correlation_scale=float(v23["correlation_scale"]),
        shared_class_fractions=v23["fractions"],
        radius_factors=v23["radius_factors"],
        optical_factors=v23["optical_factors"],
    )
    net_capacity = e.SENSITO_DENSITY_RGB[:, -1] - e.SENSITO_DMIN_RGB
    capacity = net_capacity[:, None] * e.SUBEMULSION_CAPACITY_FRACTIONS[None, :]
    rows = []
    maximum_relative_increase = 0.0
    for log_exposure in log_exposures:
        activation = e.subemulsion_activation_probabilities(
            np.full((1, 1, 3), log_exposure, dtype=np.float32)
        )[0, 0]
        common = capacity**2 * activation * (1.0 - activation)
        v23_ratio = np.sqrt(
            np.sum(common * v23_pixel, axis=-1)
            / np.maximum(np.sum(common * v23_aperture, axis=-1), 1e-30)
        )
        current_ratio = np.sqrt(
            np.sum(common * current_pixel_power, axis=-1)
            / np.maximum(
                np.sum(common * current_aperture_power, axis=-1), 1e-30
            )
        )
        relative = current_ratio / np.maximum(v23_ratio, 1e-30) - 1.0
        maximum_relative_increase = max(
            maximum_relative_increase, float(np.max(relative))
        )
        rows.append(
            {
                "log_exposure": log_exposure,
                "v23_native_pixel_to_48um_rms_ratio_rgb": v23_ratio.tolist(),
                "active_v24_inherited_ratio_rgb": current_ratio.tolist(),
                "active_relative_increase_rgb": relative.tolist(),
            }
        )
    return {
        "active_provenance": (
            "V24 fine35_integrated was selected from visual T020/T032 candidate "
            "comparisons to reduce large-cloud probability and visible opponent "
            "grain. It was never measured from a 5279 NPS."
        ),
        "v23_archive_parameters": {
            key: value.tolist() if isinstance(value, np.ndarray) else value
            for key, value in v23.items()
        },
        "rows": rows,
        "maximum_active_native_pixel_ratio_increase_over_v23": (
            maximum_relative_increase
        ),
        "interpretation": (
            "V24 moved the fixed 48 um variance toward higher native spatial "
            "frequencies. It is finer rather than more 16 mm-like geometrically, "
            "but raises point-sample density fluctuation and can make motion "
            "read harsher at insufficiently integrated display scale. V23 is "
            "not a measured fallback, so this audit does not revert it."
        ),
    }


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    calibration = np.asarray(
        [row["pre_normalization_to_published_rms_multiplier"] for row in rows],
        dtype=np.float64,
    )
    pixel_ratio = np.asarray(
        [row["predicted_native_pixel_to_48um_rms_ratio"] for row in rows],
        dtype=np.float64,
    )
    variance_shares = np.asarray(
        [row["population_48um_variance_share"] for row in rows],
        dtype=np.float64,
    )
    mean_shares = np.asarray(
        [row["population_mean_density_share"] for row in rows],
        dtype=np.float64,
    )
    return {
        "calibration_multiplier_min_rgb": np.min(calibration, axis=0).tolist(),
        "calibration_multiplier_max_rgb": np.max(calibration, axis=0).tolist(),
        "calibration_multiplier_max_over_min_rgb": (
            np.max(calibration, axis=0) / np.maximum(np.min(calibration, axis=0), 1e-30)
        ).tolist(),
        "native_pixel_to_48um_rms_ratio_min_rgb": np.min(
            pixel_ratio, axis=0
        ).tolist(),
        "native_pixel_to_48um_rms_ratio_max_rgb": np.max(
            pixel_ratio, axis=0
        ).tolist(),
        "maximum_single_population_variance_share_rgb": np.max(
            variance_shares, axis=(0, 2)
        ).tolist(),
        "maximum_single_population_mean_share_rgb": np.max(
            mean_shares, axis=(0, 2)
        ).tolist(),
    }


def site_count_degeneracy(
    log_exposures: tuple[float, ...], aperture_radius: float
) -> dict[str, object]:
    activations = np.stack(
        [
            e.subemulsion_activation_probabilities(
                np.full((1, 1, 3), x, dtype=np.float32)
            )[0, 0]
            for x in log_exposures
        ]
    )
    net_capacity = e.SENSITO_DENSITY_RGB[:, -1] - e.SENSITO_DMIN_RGB
    capacity = net_capacity[:, None] * e.SUBEMULSION_CAPACITY_FRACTIONS[None, :]
    target = np.stack(
        [
            e.published_5279_granularity_sigma(
                np.full((1, 1, 3), x, dtype=np.float32)
            )[0, 0]
            for x in log_exposures
        ]
    )
    rows = []
    for scale in (0.25, 1.0, 4.0):
        power = population_kernel_powers(
            aperture_radius=aperture_radius, site_count_scale=scale
        )
        variance = (
            capacity[None, ...] ** 2
            * activations
            * (1.0 - activations)
            * power[None, ...]
        )
        predicted = np.sqrt(np.sum(variance, axis=-1))
        multiplier = target / np.maximum(predicted, 1e-30)
        rows.append(
            {
                "site_count_scale": scale,
                "pre_normalization_sigma_range_rgb": {
                    "minimum": np.min(predicted, axis=0).tolist(),
                    "maximum": np.max(predicted, axis=0).tolist(),
                },
                "required_multiplier_range_rgb": {
                    "minimum": np.min(multiplier, axis=0).tolist(),
                    "maximum": np.max(multiplier, axis=0).tolist(),
                },
                "post_normalization_target_is_identical_by_construction": True,
            }
        )
    return {
        "rows": rows,
        "interpretation": (
            "Changing all effective site counts by 16x across the tested "
            "range changes the uncalibrated finite-site variance and higher "
            "moments, but the scalar exposure/record normalization forces the "
            "same published 48 um RMS. The public RMS curve therefore cannot "
            "identify site count or microscopic tail law."
        ),
    }


def native_spot_check(rows: list[dict[str, object]]) -> dict[str, object]:
    exposures = (-3.0, -1.0, 0.0)
    result = measure_aperture_rms(
        width=NATIVE_WIDTH_PX,
        height=192,
        log_exposures=exposures,
        first_frame_identity=7400,
        tolerance=0.03,
        profile_module=v72_profile,
    )
    predictions = {
        float(row["log_exposure"]): np.asarray(
            row["predicted_native_pixel_to_48um_rms_ratio"], dtype=np.float64
        )
        for row in rows
    }
    comparisons = []
    maximum_ratio_relative_error = 0.0
    for observed in result["rows"]:
        log_exposure = float(observed["log_exposure"])
        prediction = predictions[log_exposure]
        measured = np.asarray(
            observed["unfiltered_to_48um_ratio_rgb"], dtype=np.float64
        )
        relative = (measured - prediction) / np.maximum(prediction, 1e-30)
        maximum_ratio_relative_error = max(
            maximum_ratio_relative_error, float(np.max(np.abs(relative)))
        )
        comparisons.append(
            {
                "log_exposure": log_exposure,
                "predicted_native_pixel_to_48um_rms_ratio_rgb": prediction.tolist(),
                "measured_native_pixel_to_48um_rms_ratio_rgb": measured.tolist(),
                "ratio_relative_error_rgb": relative.tolist(),
                "measured_48um_relative_error_rgb": observed["relative_error_rgb"],
                "unfiltered_pixel_sigma_d_rgb": observed[
                    "unfiltered_pixel_sigma_d_rgb"
                ],
            }
        )
    return {
        "width": NATIVE_WIDTH_PX,
        "height": 192,
        "log_exposures": list(exposures),
        "rows": comparisons,
        "gates": {
            "maximum_48um_rms_relative_error": result["gate"],
            "maximum_analytic_pixel_ratio_relative_error": {
                "value": maximum_ratio_relative_error,
                "tolerance": 0.03,
                "pass": maximum_ratio_relative_error <= 0.03,
            },
        },
        "interpretation": (
            "The 5760-wide realization confirms that the analytic high-frequency "
            "gain is a native-image property. A 1920-wide 48 um conformance "
            "strip validates marginal RMS but rasterizes sub-population clouds "
            "differently and cannot stand in for native pixel-scale NPS."
        ),
    }


def measure(
    log_exposures: tuple[float, ...], *, include_native_spot: bool = True
) -> dict[str, object]:
    v72_profile.apply(e)
    if not np.allclose(e.SUBEMULSION_DYE_RECORD_MIX, np.eye(3)[None, ...]):
        raise RuntimeError("V74 requires V72 identity direct record formation")

    aperture_radius = (
        0.5
        * e.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
        * 1e-3
        * (NATIVE_WIDTH_PX / FILM_IMAGE_WIDTH_MM)
    )
    power_48 = population_kernel_powers(aperture_radius=aperture_radius)
    power_pixel = population_kernel_powers(aperture_radius=0.0)
    net_capacity = e.SENSITO_DENSITY_RGB[:, -1] - e.SENSITO_DMIN_RGB
    capacity = net_capacity[:, None] * e.SUBEMULSION_CAPACITY_FRACTIONS[None, :]

    rows: list[dict[str, object]] = []
    for log_exposure in log_exposures:
        field = np.full((1, 1, 3), log_exposure, dtype=np.float32)
        activation = e.subemulsion_activation_probabilities(field)[0, 0].astype(
            np.float64
        )
        mean_weight = activation * e.SUBEMULSION_CAPACITY_FRACTIONS[None, :]
        mean_share = mean_weight / np.maximum(
            np.sum(mean_weight, axis=-1, keepdims=True), 1e-30
        )
        variance_48 = (
            capacity**2 * activation * (1.0 - activation) * power_48
        )
        variance_pixel = (
            capacity**2 * activation * (1.0 - activation) * power_pixel
        )
        predicted_sigma = np.sqrt(np.sum(variance_48, axis=-1))
        target = e.published_5279_granularity_sigma(field)[0, 0].astype(np.float64)
        multiplier = target / np.maximum(predicted_sigma, 1e-30)
        variance_share = variance_48 / np.maximum(
            np.sum(variance_48, axis=-1, keepdims=True), 1e-30
        )
        pixel_ratio = np.sqrt(
            np.sum(variance_pixel, axis=-1)
            / np.maximum(np.sum(variance_48, axis=-1), 1e-30)
        )
        rows.append(
            {
                "log_exposure": log_exposure,
                "activation_probability_rgb_by_population": activation.tolist(),
                "population_mean_density_share": mean_share.tolist(),
                "population_48um_variance_share": variance_share.tolist(),
                "unscaled_predicted_48um_sigma_d_rgb": predicted_sigma.tolist(),
                "published_target_48um_sigma_d_rgb": target.tolist(),
                "pre_normalization_to_published_rms_multiplier": multiplier.tolist(),
                "predicted_native_pixel_to_48um_rms_ratio": pixel_ratio.tolist(),
                "effective_variance_population_count_rgb": (
                    1.0 / np.maximum(np.sum(variance_share**2, axis=-1), 1e-30)
                ).tolist(),
            }
        )

    pitch_um = FILM_IMAGE_WIDTH_MM * 1000.0 / NATIVE_WIDTH_PX
    physical_radius = (
        e.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB
        * e.NEGATIVE_GRAIN_CORRELATION_SCALE
        * pitch_um
    )
    report: dict[str, object] = {
        "audit": "V74 5279 fast/medium/slow activation ownership",
        "profile": v72_profile.PROFILE["name"],
        "image_change": "none",
        "fixture": {
            "record_order": list(RECORDS),
            "population_order": list(POPULATIONS),
            "log_exposures": list(log_exposures),
            "native_width_px": NATIVE_WIDTH_PX,
            "assumed_film_image_width_mm": FILM_IMAGE_WIDTH_MM,
            "native_pixel_pitch_um": pitch_um,
            "kodak_aperture_radius_px": aperture_radius,
        },
        "active_prior": {
            "speed_offsets_loge": e.SUBEMULSION_SPEED_OFFSETS_LOGE.tolist(),
            "fast_centres_loge_rgb": e.SUBEMULSION_FAST_CENTRE_LOGE_RGB.tolist(),
            "transition_width_rgb": e.SUBEMULSION_TRANSITION_WIDTH_RGB.tolist(),
            "capacity_fractions": e.SUBEMULSION_CAPACITY_FRACTIONS.tolist(),
            "site_counts_native_rgb_by_population": (
                e.SUBEMULSION_SITE_COUNT_PX_5760_RGB.tolist()
            ),
            "negative_grain_correlation_scale": (
                e.NEGATIVE_GRAIN_CORRELATION_SCALE
            ),
            "size_class_fractions": e.GRAIN_SIZE_CLASS_FRACTIONS.tolist(),
            "size_class_radius_factors": (
                e.GRAIN_SIZE_CLASS_RADIUS_FACTORS.tolist()
            ),
            "size_class_optical_factors": (
                e.GRAIN_SIZE_CLASS_OPTICAL_FACTORS.tolist()
            ),
            "morphology_provenance": (
                "inherited V24 fine35_integrated visual candidate; not a "
                "stock-specific 5279 NPS fit"
            ),
            "ecd_architecture_witness_um_rgb_by_population": (
                e.SUBEMULSION_ECD_UM_RGB.tolist()
            ),
            "effective_cloud_correlation_radius_px_rgb_by_population": (
                e.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB
                * e.NEGATIVE_GRAIN_CORRELATION_SCALE
            ).tolist(),
            "effective_cloud_correlation_radius_um_rgb_by_population": (
                physical_radius.tolist()
            ),
            "warning": (
                "ECD values supply only relative architecture. Their numeric "
                "copy into reference-pixel radii is an effective dye-cloud "
                "prior, not a physical micrometre conversion or a disclosed "
                "5279 cloud radius."
            ),
        },
        "population_kernel_power": {
            "native_pixel_rgb_by_population": power_pixel.tolist(),
            "48um_aperture_rgb_by_population": power_48.tolist(),
            "per_population_native_pixel_to_48um_rms_ratio": np.sqrt(
                power_pixel / np.maximum(power_48, 1e-30)
            ).tolist(),
        },
        "rows": rows,
        "summary": summarize_rows(rows),
        "historical_v23_to_active_v24_morphology_ablation": (
            historical_morphology_ablation(
                log_exposures, aperture_radius, power_pixel, power_48
            )
        ),
        "site_count_scale_degeneracy": site_count_degeneracy(
            log_exposures, aperture_radius
        ),
        "evidence_boundary": {
            "measured_5279": (
                "summed neutral H-D, processed MTF and per-record 48 um "
                "marginal RMS versus exposure"
            ),
            "period_mechanism": (
                "multiple speed-differentiated emulsion layers with faster "
                "layers generally farther from support"
            ),
            "not_identified": (
                "5279 population count, speed offsets, capacity fractions, "
                "site count, dye-cloud radius, population NPS and higher-order "
                "tail distribution"
            ),
        },
        "decision": (
            "The three-population organization remains a useful physical prior, "
            "but its parameters do not predict the published RMS without a "
            "large exposure/record normalization and barely identify the "
            "native-to-48um spatial ratio. Keep V72 pixels unchanged; do not "
            "interpret fast/medium/slow weights as measured 5279 layer shares."
        ),
    }
    if include_native_spot:
        report["native_5760_spot_check"] = native_spot_check(rows)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--log-exposures",
        nargs="+",
        type=float,
        default=list(DEFAULT_LOG_EXPOSURES),
    )
    parser.add_argument("--skip-native-spot", action="store_true")
    args = parser.parse_args()
    result = measure(
        tuple(args.log_exposures), include_native_spot=not args.skip_native_spot
    )
    payload = json.dumps(result, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
