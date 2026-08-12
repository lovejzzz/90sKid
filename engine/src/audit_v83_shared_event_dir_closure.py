#!/usr/bin/env python3
"""Audit shared finite activation events through stochastic 5279 DIR.

V81/V82 established one exact three-record Bernoulli family: with probability
``alpha`` a matched site in the red-, green- and blue-sensitive records tests
its own activation threshold against one common uniform variate, and otherwise
the three tests are independent.  Every marginal remains Bernoulli(p), but the
shared event introduces cross-record covariance before dye formation.

This audit propagates that covariance through the *existing* V72 five-class,
three-population spatial kernels and stochastic DIR operator in the Fourier
domain.  It reproduces the current production calibration literally: a final
record residual multiplier is applied after DIR, but its denominator is the
independent, pre-DIR variance prediction.  No additional closure repair,
clipping, image fitting or observer finish is permitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np

from emulsion5279 import legacy
import v72_profile


RECORD_NAMES = ("red", "green", "blue")
POPULATION_NAMES = ("fast", "medium", "slow")
ALPHA_ENDPOINTS = (0.0, 0.25, 0.50, 0.75, 1.0)
LOG_EXPOSURES = np.arange(-4.0, 0.751, 0.25, dtype=np.float64)
KEY_LOG_EXPOSURES = (-3.0, -2.0, -1.0, 0.0, 0.5)
FFT_SIZE = 256
RMS_RELATIVE_TOLERANCE = 0.05
MONTE_CARLO_SIZE = 384
MONTE_CARLO_CROP = 48
MONTE_CARLO_SEEDS = (83001, 83002, 83003, 83004)
MONTE_CARLO_LOG_EXPOSURE = -2.0
MONTE_CARLO_ALPHAS = (0.0, 1.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def allocate_class_counts(total_sites: int, fractions: np.ndarray) -> np.ndarray:
    """Mirror the production integer allocation exactly."""
    raw = np.asarray(fractions, dtype=np.float64) * int(total_sites)
    counts = np.maximum(np.floor(raw).astype(np.int32), 1)
    while int(np.sum(counts)) < total_sites:
        counts[int(np.argmax(raw - counts))] += 1
    while int(np.sum(counts)) > total_sites:
        removable = np.where(counts > 1, counts, 0)
        counts[int(np.argmax(removable))] -= 1
    return counts


def impulse_spectrum(
    model,
    radius: float | None = None,
    gaussian_sigma: float | None = None,
    offset: tuple[float, float] = (0.0, 0.0),
    size: int = FFT_SIZE,
) -> np.ndarray:
    """Return the discrete transfer function of the production raster ops."""
    centre = size // 2
    response = np.zeros((size, size), dtype=np.float32)
    response[centre, centre] = 1.0
    if radius is not None:
        kernel = model.disk_kernel(float(radius))
        kernel /= float(np.sum(kernel))
        response = cv2.filter2D(
            response, -1, kernel, borderType=cv2.BORDER_CONSTANT
        )
    if gaussian_sigma is not None:
        response = cv2.GaussianBlur(
            response,
            (0, 0),
            max(float(gaussian_sigma), 0.05),
            borderType=cv2.BORDER_CONSTANT,
        )
    offset_x, offset_y = offset
    if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
        transform = np.asarray(
            [[1.0, 0.0, offset_x], [0.0, 1.0, offset_y]],
            dtype=np.float32,
        )
        response = cv2.warpAffine(
            response,
            transform,
            (size, size),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
        )
    return np.fft.fft2(np.fft.ifftshift(response)).astype(np.complex128)


def build_static_spatial_model(model) -> dict[str, object]:
    """Build V72 class kernels at one native 5760-pixel film-width scale."""
    work_scale = 1.0
    aperture_radius = (
        0.5
        * float(model.KODAK_GRANULARITY_APERTURE_DIAMETER_UM)
        * 1e-3
        * (5760.0 / 24.9)
    )
    aperture = impulse_spectrum(model, radius=aperture_radius)
    aperture_power = np.square(np.abs(aperture))
    radii = (
        np.asarray(model.SUBEMULSION_CLOUD_RADIUS_PX_5760_RGB, dtype=np.float64)
        * float(model.NEGATIVE_GRAIN_CORRELATION_SCALE)
    )
    sigmas = np.asarray(
        model.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB, dtype=np.float64
    )
    site_counts = np.maximum(
        1,
        np.rint(
            np.asarray(model.SUBEMULSION_SITE_COUNT_PX_5760_RGB, dtype=np.float64)
        ).astype(np.int32),
    )
    class_fractions = np.empty((3, 5), dtype=np.float64)
    for population in range(3):
        class_fractions[population] = (
            np.asarray(model.GRAIN_SIZE_CLASS_FRACTIONS, dtype=np.float64)
            if model.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION is None
            else np.asarray(
                model.GRAIN_SIZE_CLASS_FRACTIONS_BY_POPULATION[population],
                dtype=np.float64,
            )
        )

    kernels = np.empty((3, 3, 5, FFT_SIZE, FFT_SIZE), dtype=np.complex128)
    counts = np.empty((3, 3, 5), dtype=np.int32)
    weights = np.empty((3, 3, 5), dtype=np.float64)
    radii_by_class = np.empty((3, 3, 5), dtype=np.float64)
    sigmas_by_class = np.empty((3, 3, 5), dtype=np.float64)
    offsets_by_class = np.empty((3, 3, 5, 2), dtype=np.float64)
    kernel_power_errors: list[float] = []
    for record in range(3):
        for population in range(3):
            total_sites = int(site_counts[record, population])
            class_counts = allocate_class_counts(
                total_sites, class_fractions[population]
            )
            counts[record, population] = class_counts
            weights[record, population] = class_counts / float(total_sites)
            for size_class, class_sites in enumerate(class_counts):
                class_identity = record * 15 + population * 5 + size_class
                angle = 2.0 * math.pi * (
                    (class_identity + 0.5) * float(model.GRAIN_STABLE_PHASE_STEP)
                    % 1.0
                ) + float(model.GRAIN_STABLE_PHASE_OFFSET_RADIANS)
                phase_radius = float(model.GRAIN_SUBPIXEL_PHASE_RADIUS_PX)
                offset = (
                    phase_radius * math.cos(angle),
                    phase_radius * math.sin(angle),
                )
                radius = float(
                    radii[record, population]
                    * model.GRAIN_SIZE_CLASS_RADIUS_FACTORS[size_class]
                )
                sigma = float(
                    sigmas[record, population]
                    * model.GRAIN_SIZE_CLASS_OPTICAL_FACTORS[size_class]
                )
                transfer = impulse_spectrum(
                    model, radius=radius, gaussian_sigma=sigma, offset=offset
                )
                kernels[record, population, size_class] = transfer
                radii_by_class[record, population, size_class] = radius
                sigmas_by_class[record, population, size_class] = sigma
                offsets_by_class[record, population, size_class] = offset
                fft_power = float(
                    np.sum(np.square(np.abs(transfer)) * aperture_power)
                    / (FFT_SIZE * FFT_SIZE)
                )
                spatial_power = float(
                    model.filtered_kernel_power(
                        radius, sigma, aperture_radius, offset
                    )
                )
                kernel_power_errors.append(
                    abs(fft_power - spatial_power) / max(spatial_power, 1e-30)
                )

    dir_transfer = np.stack(
        [
            impulse_spectrum(
                model,
                gaussian_sigma=float(
                    model.DIR_POPULATION_LATERAL_SIGMA_PX_5760[population]
                    * work_scale
                ),
            )
            for population in range(3)
        ],
        axis=0,
    )
    return {
        "aperture_radius": aperture_radius,
        "aperture_power": aperture_power,
        "kernels": kernels,
        "counts": counts,
        "weights": weights,
        "radii_by_class": radii_by_class,
        "sigmas_by_class": sigmas_by_class,
        "offsets_by_class": offsets_by_class,
        "dir_transfer": dir_transfer,
        "maximum_kernel_power_relative_error": max(kernel_power_errors),
    }


def joint_site_category_law(
    probabilities: np.ndarray, alpha: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return exact three-record outcome patterns for the common-U mixture."""
    probabilities = np.asarray(probabilities, dtype=np.float64)
    outcomes: dict[tuple[int, int, int], float] = {}
    for state in range(8):
        pattern = tuple((state >> record) & 1 for record in range(3))
        probability = 1.0
        for record, bit in enumerate(pattern):
            p = float(probabilities[record])
            probability *= p if bit else 1.0 - p
        outcomes[pattern] = outcomes.get(pattern, 0.0) + (1.0 - alpha) * probability

    order = np.argsort(probabilities)
    sorted_p = probabilities[order]
    interval_probabilities = (
        sorted_p[0],
        sorted_p[1] - sorted_p[0],
        sorted_p[2] - sorted_p[1],
        1.0 - sorted_p[2],
    )
    common_patterns: list[tuple[int, int, int]] = []
    for active_count in (3, 2, 1, 0):
        pattern = np.zeros(3, dtype=np.int32)
        if active_count:
            pattern[order[3 - active_count :]] = 1
        common_patterns.append(tuple(int(value) for value in pattern))
    for pattern, probability in zip(
        common_patterns, interval_probabilities, strict=True
    ):
        outcomes[pattern] = outcomes.get(pattern, 0.0) + alpha * float(probability)

    patterns = np.asarray(list(outcomes), dtype=np.int32)
    category_probabilities = np.asarray(
        [outcomes[tuple(pattern)] for pattern in patterns], dtype=np.float64
    )
    category_probabilities /= np.sum(category_probabilities)
    return patterns, category_probabilities


def shared_binomial_fractions(
    probabilities: np.ndarray,
    site_counts: np.ndarray,
    alpha: float,
    rng: np.random.Generator,
    shape: tuple[int, int],
) -> np.ndarray:
    """Sample exact common-alpha matched sites plus independent extra sites."""
    probabilities = np.asarray(probabilities, dtype=np.float64)
    site_counts = np.asarray(site_counts, dtype=np.int32)
    matched = int(np.min(site_counts))
    patterns, category_probabilities = joint_site_category_law(
        probabilities, alpha
    )
    category_counts = rng.multinomial(
        matched, category_probabilities, size=shape
    )
    developed = np.tensordot(
        category_counts, patterns, axes=([-1], [0])
    ).astype(np.int32)
    for record in range(3):
        remainder = int(site_counts[record] - matched)
        if remainder:
            developed[..., record] += rng.binomial(
                remainder, float(probabilities[record]), size=shape
            ).astype(np.int32)
    return developed.astype(np.float32) / site_counts[None, None, :]


def monte_carlo_verification(
    model,
    static: dict[str, object],
    analytic_row: dict[str, object],
) -> dict[str, object]:
    """Directly sample two endpoints to catch transfer/algebra mistakes."""
    shape = (MONTE_CARLO_SIZE, MONTE_CARLO_SIZE)
    probabilities = model.subemulsion_activation_probabilities(
        np.full((3,), MONTE_CARLO_LOG_EXPOSURE, dtype=np.float32)
    ).astype(np.float64)
    activations = np.broadcast_to(
        probabilities[None, None, ...], shape + (3, 3)
    ).astype(np.float32)
    capacities = (
        np.asarray(model.SENSITO_DENSITY_RGB[:, -1], dtype=np.float64)
        - np.asarray(model.SENSITO_DMIN_RGB, dtype=np.float64)
    )[:, None] * np.asarray(model.SUBEMULSION_CAPACITY_FRACTIONS, dtype=np.float64)[
        None, :
    ]
    calibration = np.asarray(
        analytic_row["production_post_coupling_residual_calibration_rgb"],
        dtype=np.float64,
    )
    aperture_radius = float(static["aperture_radius"])
    aperture = model.disk_kernel(aperture_radius)
    aperture /= float(np.sum(aperture))

    alpha_rows: dict[str, object] = {}
    for alpha in MONTE_CARLO_ALPHAS:
        all_samples: list[np.ndarray] = []
        for seed in MONTE_CARLO_SEEDS:
            rng = np.random.default_rng(seed + int(alpha * 1000.0))
            layers = np.zeros(shape + (3, 3), dtype=np.float32)
            for population in range(3):
                for size_class in range(5):
                    class_counts = static["counts"][:, population, size_class]
                    developed = shared_binomial_fractions(
                        probabilities[:, population],
                        class_counts,
                        alpha,
                        rng,
                        shape,
                    )
                    for record in range(3):
                        value = cv2.filter2D(
                            developed[..., record],
                            -1,
                            model.disk_kernel(
                                float(
                                    static["radii_by_class"][
                                        record, population, size_class
                                    ]
                                )
                            )
                            / float(
                                np.sum(
                                    model.disk_kernel(
                                        float(
                                            static["radii_by_class"][
                                                record, population, size_class
                                            ]
                                        )
                                    )
                                )
                            ),
                            borderType=cv2.BORDER_REFLECT,
                        )
                        value = cv2.GaussianBlur(
                            value,
                            (0, 0),
                            max(
                                float(
                                    static["sigmas_by_class"][
                                        record, population, size_class
                                    ]
                                ),
                                0.05,
                            ),
                            borderType=cv2.BORDER_REFLECT,
                        )
                        deviation = value - float(probabilities[record, population])
                        offset_x, offset_y = static["offsets_by_class"][
                            record, population, size_class
                        ]
                        if abs(offset_x) > 1e-6 or abs(offset_y) > 1e-6:
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
                            float(
                                static["weights"][
                                    record, population, size_class
                                ]
                            )
                            * deviation
                        )
            coupled = model.couple_5279_population_deviations(
                layers, activations, 1.0
            )
            density = np.sum(
                coupled * capacities[None, None, ...], axis=-1
            )
            density *= calibration[None, None, :]
            filtered = np.stack(
                [
                    cv2.filter2D(
                        density[..., record],
                        -1,
                        aperture,
                        borderType=cv2.BORDER_REFLECT,
                    )
                    for record in range(3)
                ],
                axis=-1,
            )
            interior = filtered[
                MONTE_CARLO_CROP:-MONTE_CARLO_CROP,
                MONTE_CARLO_CROP:-MONTE_CARLO_CROP,
            ]
            all_samples.append(interior.reshape(-1, 3).astype(np.float64))

        samples = np.concatenate(all_samples, axis=0)
        samples -= np.mean(samples, axis=0, keepdims=True)
        covariance = samples.T @ samples / float(samples.shape[0] - 1)
        analytic = np.asarray(
            analytic_row["alpha_endpoints"][str(alpha)][
                "after_stochastic_dir"
            ]["covariance_density"],
            dtype=np.float64,
        )
        measured_sigma = np.sqrt(np.diag(covariance))
        analytic_sigma = np.sqrt(np.diag(analytic))
        measured_correlation = covariance / np.outer(
            measured_sigma, measured_sigma
        )
        analytic_correlation = analytic / np.outer(
            analytic_sigma, analytic_sigma
        )
        alpha_rows[str(alpha)] = {
            "sample_count": int(samples.shape[0]),
            "measured": covariance_summary(covariance),
            "analytic": covariance_summary(analytic),
            "maximum_sigma_relative_error": float(
                np.max(np.abs(measured_sigma / analytic_sigma - 1.0))
            ),
            "maximum_correlation_absolute_error": float(
                np.max(np.abs(measured_correlation - analytic_correlation))
            ),
        }
    return {
        "log_exposure": MONTE_CARLO_LOG_EXPOSURE,
        "patch_dimensions": [MONTE_CARLO_SIZE, MONTE_CARLO_SIZE],
        "crop_pixels_per_edge": MONTE_CARLO_CROP,
        "seeds": list(MONTE_CARLO_SEEDS),
        "alpha_endpoints": alpha_rows,
        "purpose": (
            "Verification only: direct finite multinomial/binomial samples catch "
            "frequency-transfer or matrix-indexing mistakes; the analytic integral "
            "remains the deterministic audit authority."
        ),
    }


def aperture_covariance(
    spectrum: np.ndarray, aperture_power: np.ndarray
) -> np.ndarray:
    """Integrate a 3x3 cross-power spectrum through the 48 um aperture."""
    covariance = np.sum(
        spectrum * aperture_power[..., None, None], axis=(0, 1)
    ).real / float(FFT_SIZE * FFT_SIZE)
    return 0.5 * (covariance + covariance.T)


def covariance_summary(covariance: np.ndarray) -> dict[str, object]:
    covariance = np.asarray(covariance, dtype=np.float64)
    sigma = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    correlation = covariance / np.maximum(np.outer(sigma, sigma), 1e-30)
    return {
        "sigma_density_rgb": sigma.tolist(),
        "covariance_density": covariance.tolist(),
        "correlation": correlation.tolist(),
        "minimum_covariance_eigenvalue": float(np.min(np.linalg.eigvalsh(covariance))),
    }


def row_for_exposure(
    model, static: dict[str, object], log_exposure: float
) -> dict[str, object]:
    probabilities = model.subemulsion_activation_probabilities(
        np.full((3,), log_exposure, dtype=np.float32)
    ).astype(np.float64)
    target = model.published_5279_granularity_sigma(
        np.full((3,), log_exposure, dtype=np.float32)
    ).astype(np.float64)
    capacities = (
        np.asarray(model.SENSITO_DENSITY_RGB[:, -1], dtype=np.float64)
        - np.asarray(model.SENSITO_DMIN_RGB, dtype=np.float64)
    )[:, None] * np.asarray(model.SUBEMULSION_CAPACITY_FRACTIONS, dtype=np.float64)[
        None, :
    ]
    kernels = static["kernels"]
    counts = static["counts"]
    weights = static["weights"]
    aperture_power = static["aperture_power"]

    # Source cross-power is block diagonal by speed population.  ``shared_base``
    # is the alpha=1 common-uniform contribution; diagonal marginal power never
    # depends on alpha.
    marginal = np.empty((3, 3, FFT_SIZE, FFT_SIZE), dtype=np.float64)
    shared_base = np.zeros(
        (3, 3, 3, FFT_SIZE, FFT_SIZE), dtype=np.complex128
    )
    for population in range(3):
        for record in range(3):
            p = float(probabilities[record, population])
            value = np.zeros((FFT_SIZE, FFT_SIZE), dtype=np.float64)
            for size_class in range(5):
                h = kernels[record, population, size_class]
                n = int(counts[record, population, size_class])
                w = float(weights[record, population, size_class])
                value += w * w * p * (1.0 - p) / n * np.square(np.abs(h))
            marginal[record, population] = value
            shared_base[population, record, record] = value
        for left in range(3):
            for right in range(left + 1, 3):
                p = float(probabilities[left, population])
                q = float(probabilities[right, population])
                joint_covariance = min(p, q) - p * q
                value = np.zeros((FFT_SIZE, FFT_SIZE), dtype=np.complex128)
                for size_class in range(5):
                    n_left = int(counts[left, population, size_class])
                    n_right = int(counts[right, population, size_class])
                    matched = min(n_left, n_right)
                    w_left = float(weights[left, population, size_class])
                    w_right = float(weights[right, population, size_class])
                    h_left = kernels[left, population, size_class]
                    h_right = kernels[right, population, size_class]
                    value += (
                        w_left
                        * w_right
                        * matched
                        * joint_covariance
                        / (n_left * n_right)
                        * h_left
                        * np.conjugate(h_right)
                    )
                shared_base[population, left, right] = value
                shared_base[population, right, left] = np.conjugate(value)

    predicted_before_dir = np.asarray(
        [
            sum(
                capacities[record, population] ** 2
                * np.sum(
                    marginal[record, population] * aperture_power
                )
                / (FFT_SIZE * FFT_SIZE)
                for population in range(3)
            )
            for record in range(3)
        ],
        dtype=np.float64,
    )
    production_residual_calibration = target / np.sqrt(
        np.maximum(predicted_before_dir, 1e-30)
    )

    # C maps the nine uncalibrated layer deviations to three final density
    # records through stochastic intralayer and interimage DIR.
    c_transfer = np.zeros(
        (FFT_SIZE, FFT_SIZE, 3, 9), dtype=np.complex128
    )
    activation_marginal = np.clip(
        4.0 * probabilities * (1.0 - probabilities), 0.0, 1.0
    )
    for source_record in range(3):
        for source_population in range(3):
            source_index = source_record * 3 + source_population
            g = static["dir_transfer"][source_population]
            self_response = 1.0 + (
                float(model.DIR_STOCHASTIC_COUPLING_SCALE)
                * float(
                    model.DIR_DEVELOPMENT_INTRALAYER_STRENGTH_RGB[source_record]
                )
                * activation_marginal[source_record, source_population]
                * (1.0 - g)
            )
            c_transfer[..., source_record, source_index] += (
                capacities[source_record, source_population] * self_response
            )
            for destination_record in range(3):
                record_transport = float(
                    model.DIR_INTERIMAGE_RECEIVER_CAUSER[
                        destination_record, source_record
                    ]
                )
                if record_transport <= 0.0:
                    continue
                for destination_population in range(3):
                    transport = (
                        float(model.DIR_STOCHASTIC_COUPLING_SCALE)
                        * float(model.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH)
                        * record_transport
                        * float(
                            model.DIR_POPULATION_TRANSPORT[
                                destination_population, source_population
                            ]
                        )
                        * float(
                            model.DIR_POPULATION_RELEASE_GAIN[source_population]
                        )
                        * float(
                            model.DIR_POPULATION_RECEIVER_GAIN[
                                destination_population
                            ]
                        )
                    )
                    c_transfer[
                        ..., destination_record, source_index
                    ] -= (
                        capacities[destination_record, destination_population]
                        * transport
                        * activation_marginal[
                            destination_record, destination_population
                        ]
                        * g
                    )

    alpha_rows: dict[str, object] = {}
    for alpha in ALPHA_ENDPOINTS:
        output_spectrum = np.zeros(
            (FFT_SIZE, FFT_SIZE, 3, 3), dtype=np.complex128
        )
        before_dir_spectrum = np.zeros_like(output_spectrum)
        minimum_source_eigenvalue = math.inf
        for population in range(3):
            source = np.array(shared_base[population], copy=True)
            for left in range(3):
                for right in range(3):
                    if left != right:
                        source[left, right] *= alpha
            # Reorder the matrix axes for batched eigensolvers/einsum.
            source_hw = np.moveaxis(source, (0, 1), (-2, -1))
            minimum_source_eigenvalue = min(
                minimum_source_eigenvalue,
                float(np.min(np.linalg.eigvalsh(source_hw))),
            )
            indices = [record * 3 + population for record in range(3)]
            c = c_transfer[..., :, indices]
            output_spectrum += np.einsum(
                "...ir,...rs,...js->...ij",
                c,
                source_hw,
                np.conjugate(c),
                optimize=True,
            )
            b = np.zeros_like(c)
            for record in range(3):
                b[..., record, record] = capacities[record, population]
            before_dir_spectrum += np.einsum(
                "...ir,...rs,...js->...ij",
                b,
                source_hw,
                np.conjugate(b),
                optimize=True,
            )

        raw_before_covariance = aperture_covariance(
            before_dir_spectrum, aperture_power
        )
        raw_after_covariance = aperture_covariance(
            output_spectrum, aperture_power
        )
        calibration_outer = np.outer(
            production_residual_calibration,
            production_residual_calibration,
        )
        before_covariance = raw_before_covariance * calibration_outer
        after_covariance = raw_after_covariance * calibration_outer
        before_sigma = np.sqrt(np.maximum(np.diag(before_covariance), 0.0))
        after_sigma = np.sqrt(np.maximum(np.diag(after_covariance), 0.0))
        relative_error = after_sigma / target - 1.0
        alpha_rows[str(alpha)] = {
            "source_spectrum_minimum_eigenvalue": minimum_source_eigenvalue,
            "raw_before_dir": covariance_summary(raw_before_covariance),
            "raw_after_stochastic_dir": covariance_summary(raw_after_covariance),
            "before_dir": covariance_summary(before_covariance),
            "after_stochastic_dir": covariance_summary(after_covariance),
            "target_sigma_density_rgb": target.tolist(),
            "after_dir_relative_error_rgb": relative_error.tolist(),
            "maximum_after_dir_absolute_relative_error": float(
                np.max(np.abs(relative_error))
            ),
            "passes_five_percent_rms_gate": bool(
                np.max(np.abs(relative_error)) <= RMS_RELATIVE_TOLERANCE
            ),
            "production_post_coupling_residual_calibration_applied": True,
            "additional_post_density_repair": False,
        }

    return {
        "log_exposure": log_exposure,
        "activation_probability_by_record_population": {
            RECORD_NAMES[record]: {
                POPULATION_NAMES[population]: float(
                    probabilities[record, population]
                )
                for population in range(3)
            }
            for record in range(3)
        },
        "target_sigma_density_rgb": target.tolist(),
        "production_post_coupling_residual_calibration_rgb": (
            production_residual_calibration.tolist()
        ),
        "alpha_endpoints": alpha_rows,
    }


def measure(script_path: Path) -> dict[str, object]:
    v72_profile.apply(legacy.model)
    model = legacy.model
    if model.GRAIN_CALIBRATION_DOMAIN != "post_coupling_residual":
        raise RuntimeError("V72 must retain post-coupling residual calibration")
    if model.GRAIN_SUBPIXEL_PHASE_MODE != "stable_balanced":
        raise RuntimeError("V72 must retain stable balanced class phases")
    if not np.array_equal(
        model.SUBEMULSION_DYE_RECORD_MIX,
        np.repeat(np.eye(3, dtype=np.float32)[None, ...], 3, axis=0),
    ):
        raise RuntimeError("V72 must use identity source-to-record mixing")

    static = build_static_spatial_model(model)
    rows = [
        row_for_exposure(model, static, float(log_exposure))
        for log_exposure in LOG_EXPOSURES
    ]
    monte_carlo_row = next(
        row
        for row in rows
        if abs(row["log_exposure"] - MONTE_CARLO_LOG_EXPOSURE) < 1e-12
    )
    monte_carlo = monte_carlo_verification(model, static, monte_carlo_row)
    summary: dict[str, object] = {}
    for alpha in ALPHA_ENDPOINTS:
        endpoint_rows = [row["alpha_endpoints"][str(alpha)] for row in rows]
        errors = np.asarray(
            [endpoint["after_dir_relative_error_rgb"] for endpoint in endpoint_rows],
            dtype=np.float64,
        )
        pass_rows = [
            endpoint["passes_five_percent_rms_gate"] for endpoint in endpoint_rows
        ]
        summary[str(alpha)] = {
            "passing_exposure_count": int(np.sum(pass_rows)),
            "total_exposure_count": len(rows),
            "maximum_absolute_relative_error": float(np.max(np.abs(errors))),
            "maximum_absolute_relative_error_by_record": np.max(
                np.abs(errors), axis=0
            ).tolist(),
            "mean_signed_relative_error_by_record": np.mean(errors, axis=0).tolist(),
            "worst_log_exposure_by_record": [
                float(LOG_EXPOSURES[int(np.argmax(np.abs(errors[:, record])))])
                for record in range(3)
            ],
            "minimum_source_spectrum_eigenvalue": float(
                min(
                    endpoint["source_spectrum_minimum_eigenvalue"]
                    for endpoint in endpoint_rows
                )
            ),
        }

    all_shared_pass = all(
        summary[str(alpha)]["passing_exposure_count"] == len(rows)
        for alpha in ALPHA_ENDPOINTS[1:]
    )
    return {
        "audit": "V83 shared finite events through stochastic DIR",
        "profile": "V72 evidence-minimal record formation",
        "image_change": "none; exact second-order pre-render gate only",
        "spatial_model": {
            "fft_size": FFT_SIZE,
            "native_film_width_pixels": 5760,
            "film_width_mm": 24.9,
            "aperture_diameter_um": float(
                model.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
            ),
            "aperture_radius_pixels": static["aperture_radius"],
            "maximum_fft_vs_spatial_kernel_power_relative_error": static[
                "maximum_kernel_power_relative_error"
            ],
            "production_operators_reproduced": [
                "five finite-site size classes",
                "record/population-specific dye-cloud disks",
                "record/population-specific Gaussian optical integration",
                "stable balanced subpixel class phases",
                "three stochastic DIR diffusion lengths",
                "intralayer high-pass inhibitor response",
                "interimage low-pass inhibitor transport",
                "identity V72 record summation",
                "Kodak 48 micrometre circular aperture",
            ],
        },
        "shared_event_model": {
            "construction": (
                "For matched same-population/same-size-class sites, alpha selects "
                "one common U(0,1); 1-alpha selects independent uniforms. Extra "
                "sites in a record remain independent."
            ),
            "marginals": "exact finite Bernoulli/binomial for every record",
            "cross_covariance_per_matched_site": (
                "alpha * (min(p_i,p_j) - p_i*p_j)"
            ),
            "production_post_coupling_residual_calibration": True,
            "calibration_denominator_includes_dir": False,
            "calibration_denominator_includes_cross_record_covariance": False,
            "additional_post_density_rescaling": False,
            "density_clipping_in_this_audit": False,
            "physical_site_registration_is_measured": False,
        },
        "rms_gate": {
            "relative_tolerance": RMS_RELATIVE_TOLERANCE,
            "authority": "digitized Kodak processed-stock diffuse RMS graph",
            "note": (
                "Five percent is an explicit engineering gate, not a tolerance "
                "published by Kodak; the source graph itself is visually digitized."
            ),
        },
        "alpha_summary": summary,
        "monte_carlo_verification": monte_carlo,
        "key_exposure_rows": {
            str(value): next(
                row for row in rows if abs(row["log_exposure"] - value) < 1e-12
            )
            for value in KEY_LOG_EXPOSURES
        },
        "all_exposure_rows": rows,
        "decision": (
            "The shared-event family passes the pre-render marginal-RMS gate at "
            "every tested alpha/exposure endpoint. It may proceed only to an "
            "explicitly labelled uncertainty render; no alpha is identified as "
            "5279."
            if all_shared_pass
            else "At least one nonzero shared-event endpoint violates the pre-render "
            "processed 48-micrometre RMS gate after stochastic DIR. Do not promote "
            "the family into production or repair completed density to hide the "
            "failure; narrow or reject the offending alpha range first."
        ),
        "evidence_boundary": (
            "Public 5279 material publishes marginal processed-record RMS, not "
            "cross-record covariance, native NPS, physical site registration or a "
            "joint three-record event law. Passing this audit proves internal "
            "compatibility only; it does not measure a 5279 alpha."
        ),
        "provenance": {
            "script": str(script_path),
            "script_sha256": sha256(script_path),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = measure(Path(__file__))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["alpha_summary"], indent=2))
    print(report["decision"])


if __name__ == "__main__":
    main()
