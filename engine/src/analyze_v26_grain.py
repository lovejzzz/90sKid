#!/usr/bin/env python3
"""Measure V25/V26 exposure-conditioned grain spectra without display grading."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np

import emulsion_experiment as e
import v25_profile
import v26_profile


EXPOSURES = (-3.0, -2.0, -0.75)
EXPOSURE_NAMES = ("shadow", "mid", "highlight")
CHANNEL_NAMES = ("R / cyan record", "G / magenta record", "B / yellow record")
CURVE_COLORS = ("#6f8190", "#c36a4a", "#e3b34a")


def apply_profile(name: str) -> None:
    v25_profile.apply(e)
    e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION = None
    if name == "v26":
        v26_profile.apply(e)


def class_counts(total_sites: int, fractions: np.ndarray) -> np.ndarray:
    raw = fractions * total_sites
    counts = np.maximum(np.floor(raw).astype(np.int32), 1)
    while int(counts.sum()) < total_sites:
        counts[int(np.argmax(raw - counts))] += 1
    while int(counts.sum()) > total_sites:
        removable = np.where(counts > 1, counts, 0)
        counts[int(np.argmax(removable))] -= 1
    return counts


def cloud_power(radius: float, sigma: float, size: int) -> np.ndarray:
    impulse = np.zeros((size, size), dtype=np.float32)
    impulse[size // 2, size // 2] = 1.0
    kernel = e.disk_kernel(radius)
    kernel /= float(kernel.sum())
    response = cv2.filter2D(impulse, -1, kernel, borderType=cv2.BORDER_CONSTANT)
    response = cv2.GaussianBlur(
        response, (0, 0), max(float(sigma), 0.05), borderType=cv2.BORDER_CONSTANT
    )
    spectrum = np.fft.fftshift(np.fft.fft2(np.fft.ifftshift(response)))
    return np.square(np.abs(spectrum)).astype(np.float64)


def radial_profile(power: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    size = power.shape[0]
    yy, xx = np.indices(power.shape)
    radius = np.hypot(xx - size // 2, yy - size // 2)
    bins = np.floor(radius).astype(np.int32)
    radial_sum = np.bincount(bins.ravel(), weights=power.ravel())
    radial_count = np.bincount(bins.ravel())
    profile = radial_sum / np.maximum(radial_count, 1)
    cycles_per_mm = np.arange(profile.size) / size * (5760.0 / 24.9)
    valid = cycles_per_mm <= 115.0
    return cycles_per_mm[valid], profile[valid]


def spectrum_for(profile: str, loge: float, channel: int, size: int = 512):
    apply_profile(profile)
    log_exposure = np.full((1, 1, 3), loge, dtype=np.float32)
    activations = e.subemulsion_activation_probabilities(log_exposure)[0, 0]
    capacities = (
        (e.SENSITO_DENSITY_RGB[:, -1] - e.SENSITO_DMIN_RGB)[:, None]
        * e.SUBEMULSION_CAPACITY_FRACTIONS[None, :]
    )
    total_power = np.zeros((size, size), dtype=np.float64)
    population_power = np.zeros(3, dtype=np.float64)
    population_radius_power = np.zeros(3, dtype=np.float64)

    for population in range(3):
        fractions = (
            e.GRAIN_SIZE_CLASS_FRACTIONS
            if e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION is None
            else e.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION[population]
        )
        total_sites = int(e.SUBEMULSION_SITE_COUNT_PX_5760_RGB[channel, population])
        counts = class_counts(total_sites, fractions)
        p = float(activations[channel, population])
        base_variance = (
            float(capacities[channel, population]) ** 2
            * p
            * (1.0 - p)
            * float(e.SUBEMULSION_DYE_RECORD_MIX[population, channel, channel]) ** 2
        )
        for size_class, sites in enumerate(counts):
            weight = float(sites) / total_sites
            radius = (
                float(e.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB[channel, population])
                * float(e.NEGATIVE_GRAIN_CORRELATION_SCALE)
                * float(e.GRAIN_SIZE_CLASS_RADIUS_FACTORS[size_class])
            )
            sigma = (
                float(e.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB[channel, population])
                * float(e.GRAIN_SIZE_CLASS_OPTICAL_FACTORS[size_class])
            )
            coefficient = base_variance * weight * weight / float(sites)
            component = coefficient * cloud_power(radius, sigma, size)
            total_power += component
            scalar_power = float(component.sum())
            population_power[population] += scalar_power
            population_radius_power[population] += scalar_power * radius

    freq, radial = radial_profile(total_power)
    radial /= max(float(np.trapz(radial, freq)), 1e-20)
    population_fraction = population_power / max(float(population_power.sum()), 1e-20)
    effective_radius = float(population_radius_power.sum() / max(population_power.sum(), 1e-20))
    low = float(np.trapz(radial[freq <= 10], freq[freq <= 10]))
    high = float(np.trapz(radial[freq >= 40], freq[freq >= 40]))
    centroid = float(np.trapz(radial * freq, freq))
    return {
        "frequency_cycles_per_mm": freq,
        "radial_nps": radial,
        "population_power_fraction": population_fraction,
        "effective_radius_px_at_5760": effective_radius,
        "low_frequency_share_below_10_cy_mm": low,
        "high_frequency_share_above_40_cy_mm": high,
        "spectral_centroid_cycles_per_mm": centroid,
    }


def temporal_and_mean_check(profile: str) -> dict[str, float]:
    apply_profile(profile)
    # This compact flat field tests stochastic expectation and frame independence.
    # It is not used for spatial-frequency calibration, which is calculated at
    # the native 5760 px / 24.9 mm sampling above.
    loge = -2.0
    records = np.full((384, 512, 3), 10.0 ** (loge + 1.0), dtype=np.float32)
    mean = e.develop_5279_record_density(records)
    deviations = []
    for frame in (120, 121, 122, 123):
        formed = e.form_5279_multilayer_record_density(
            records, frame, grain_scale=1.0, oversample=1, precomputed_mean_density=mean
        )
        deviations.append((formed - mean)[24:-24, 24:-24].astype(np.float64))
    stacked = np.stack(deviations)
    frame_means = stacked.mean(axis=(1, 2))
    lag_correlations = []
    for left, right in zip(stacked[:-1], stacked[1:]):
        for channel in range(3):
            lag_correlations.append(
                float(np.corrcoef(left[..., channel].ravel(), right[..., channel].ravel())[0, 1])
            )
    return {
        "maximum_absolute_density_mean_drift": float(np.max(np.abs(frame_means))),
        "maximum_absolute_lag1_correlation": float(np.max(np.abs(lag_correlations))),
        "mean_absolute_lag1_correlation": float(np.mean(np.abs(lag_correlations))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    results: dict[str, object] = {"profiles": {}, "checks": {}}
    spectra = {}
    for profile in ("v25", "v26"):
        profile_rows = {}
        for name, loge in zip(EXPOSURE_NAMES, EXPOSURES):
            channel_rows = []
            for channel in range(3):
                row = spectrum_for(profile, loge, channel)
                spectra[(profile, name, channel)] = row
                channel_rows.append(
                    {
                        key: value.tolist() if isinstance(value, np.ndarray) else value
                        for key, value in row.items()
                        if key not in ("frequency_cycles_per_mm", "radial_nps")
                    }
                )
            profile_rows[name] = {"log_exposure": loge, "channels": channel_rows}
        results["profiles"][profile] = profile_rows
        results["checks"][profile] = temporal_and_mean_check(profile)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.7), sharey=True)
    for exposure_index, (axis, name, loge) in enumerate(zip(axes, EXPOSURE_NAMES, EXPOSURES)):
        for profile, style in (("v25", "--"), ("v26", "-")):
            row = spectra[(profile, name, 1)]
            axis.plot(
                row["frequency_cycles_per_mm"],
                row["radial_nps"],
                linestyle=style,
                color=CURVE_COLORS[exposure_index],
                linewidth=2.2,
                label=profile.upper(),
            )
        axis.set_title(f"{name.title()} · logE {loge:+.2f}")
        axis.set_xlim(0, 100)
        axis.set_xlabel("Spatial frequency (cycles/mm)")
        axis.grid(alpha=0.18)
        axis.legend(frameon=False)
    axes[0].set_ylabel("Normalized radial dye-density NPS")
    fig.suptitle("5279 green-record grain spectrum · V25 shared vs V26 exposure-conditioned classes")
    fig.tight_layout()
    fig.savefig(args.output / "v26_grain_nps.png", dpi=180, facecolor="#f2efe8")
    plt.close(fig)

    apply_profile("v26")
    exposure_axis = np.linspace(-4.0, 0.5, 301, dtype=np.float32)
    activation = e.subemulsion_activation_probabilities(
        np.repeat(exposure_axis[:, None], 3, axis=1)
    )[:, 1, :]
    marginal_noise = activation * (1.0 - activation)
    marginal_noise /= np.maximum(marginal_noise.sum(axis=1, keepdims=True), 1e-12)
    fig, axis = plt.subplots(figsize=(9.5, 5.3))
    for population, label, color in zip(range(3), ("Fast", "Medium", "Slow"), ("#9b5746", "#b89a55", "#647c78")):
        axis.plot(exposure_axis, marginal_noise[:, population], label=label, color=color, linewidth=2.4)
    axis.set_xlabel("Log exposure")
    axis.set_ylabel("Fraction of local binomial variance")
    axis.set_title("Exposure selects different physical sub-emulsions")
    axis.grid(alpha=0.18)
    axis.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output / "v26_layer_variance_activation.png", dpi=180, facecolor="#f2efe8")
    plt.close(fig)

    (args.output / "v26_grain_diagnostics.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(results["checks"], indent=2))


if __name__ == "__main__":
    main()
