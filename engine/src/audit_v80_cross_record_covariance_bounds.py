#!/usr/bin/env python3
"""Bound the missing 5279 cross-record covariance without fitting an image.

Kodak's three 48 um granularity curves constrain marginal record RMS but not
cross-record spatial covariance.  This audit applies frequency-band covariance
transforms to one already formed V72 density residual, then restores each
record's original 48 um RMS exactly.  The resulting equicorrelation family is a
second-order uncertainty interval, not a coating model or proposed stock value.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from audit_v75_scale_integrated_delivery import exact_integer_area
from audit_v79_projection_grain_policy_ownership import (
    FRAME_WIDTH_MM,
    LUMA,
    luma_opponent_rms,
    mean_relative_tail_or_none,
    publish_policy,
    render_local_endpoint,
)
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import ProResRawDecoder
from emulsion5279.pipeline import Emulsion5279Engine, FormedNegative


RHO_ENDPOINTS = (0.0, 0.50, 0.80, 0.90, 0.95, 0.98, 0.99, 0.995, 0.999)
FREQUENCY_EDGES_LP_MM = np.asarray(
    [0.0, 4.0, 8.0, 12.0, 16.0, 24.0, 32.0, 40.0, 48.0,
     64.0, 80.0, 96.0, 116.0, 170.0],
    dtype=np.float64,
)


def symmetric_power(matrix: np.ndarray, exponent: float) -> np.ndarray:
    values, vectors = np.linalg.eigh(np.asarray(matrix, dtype=np.float64))
    floor = max(float(np.max(values)) * 1e-10, 1e-20)
    powered = np.power(np.maximum(values, floor), exponent)
    return (vectors * powered[None, :]) @ vectors.T


def covariance_and_correlation(samples: np.ndarray) -> dict[str, object]:
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


def weighted_complex_gram(
    coefficients: np.ndarray, weights: np.ndarray
) -> np.ndarray:
    """Small 3x3 Gram matrix without platform complex-BLAS FP flag leakage."""
    result = np.empty((3, 3), dtype=np.float64)
    denominator = float(np.sum(weights))
    for row in range(3):
        for column in range(3):
            result[row, column] = float(
                np.sum(
                    np.conjugate(coefficients[:, row])
                    * coefficients[:, column]
                    * weights,
                    dtype=np.complex128,
                ).real
                / denominator
            )
    return result


def filter_48um(residual: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    pixels_per_mm = residual.shape[1] / FRAME_WIDTH_MM
    radius = pixels_per_mm * 0.024
    aperture = e.disk_kernel(radius)
    aperture /= float(np.sum(aperture))
    filtered = np.stack(
        [
            cv2.filter2D(
                residual[..., channel],
                -1,
                aperture,
                borderType=cv2.BORDER_REFLECT,
            )
            for channel in range(3)
        ],
        axis=-1,
    ).astype(np.float32)
    margin = max(24, aperture.shape[0] * 4)
    interior = filtered[margin:-margin, margin:-margin]
    return interior, {
        "diameter_um": 48.0,
        "radius_pixels": radius,
        "kernel_shape": list(aperture.shape),
        "interior_dimensions": [interior.shape[1], interior.shape[0]],
    }


def bandwise_equicorrelation(
    residual: np.ndarray, rho: float
) -> tuple[np.ndarray, dict[str, object]]:
    """Change only band-integrated joint covariance before RMS closure."""
    field = np.asarray(residual, dtype=np.float64)
    height, width = field.shape[:2]
    pixels_per_mm = width / FRAME_WIDTH_MM
    spectrum = np.fft.rfft2(field, axes=(0, 1))
    transformed = spectrum.copy()
    fy = np.fft.fftfreq(height)[:, None] * pixels_per_mm
    fx = np.fft.rfftfreq(width)[None, :] * pixels_per_mm
    radius = np.sqrt(fx * fx + fy * fy)
    band_rows: list[dict[str, object]] = []
    for low, high in zip(
        FREQUENCY_EDGES_LP_MM[:-1],
        FREQUENCY_EDGES_LP_MM[1:],
        strict=True,
    ):
        mask = (radius >= low) & (radius < high)
        if low == 0.0:
            mask[0, 0] = False
        coefficients = spectrum[mask]
        if coefficients.shape[0] < 3:
            continue
        coefficient_scale = float(np.max(np.abs(coefficients)))
        if not np.isfinite(coefficient_scale) or coefficient_scale <= 1e-30:
            continue
        # Normalize each band before its tiny 3x3 products.  The covariance
        # operator is invariant to a common scale, while this avoids BLAS
        # overflow/underflow flags on very low- or high-energy FFT bands.
        normalized = coefficients / coefficient_scale
        weights = np.ones(coefficients.shape[0], dtype=np.float64)
        x_indices = np.nonzero(mask)[1]
        doubled = (x_indices != 0) & (
            (width % 2 != 0) | (x_indices != width // 2)
        )
        weights[doubled] = 2.0
        covariance = weighted_complex_gram(normalized, weights)
        sigma = np.sqrt(np.maximum(np.diag(covariance), 1e-30))
        target_correlation = np.full((3, 3), float(rho), dtype=np.float64)
        np.fill_diagonal(target_correlation, 1.0)
        target = np.outer(sigma, sigma) * target_correlation
        operator = symmetric_power(covariance, -0.5) @ symmetric_power(
            target, 0.5
        )
        output_normalized = np.sum(
            normalized[:, :, None] * operator[None, :, :], axis=1
        )
        output_coefficients = output_normalized * coefficient_scale
        transformed[mask] = output_coefficients
        achieved = weighted_complex_gram(output_normalized, weights)
        achieved_sigma = np.sqrt(np.maximum(np.diag(achieved), 1e-30))
        achieved_correlation = achieved / np.outer(
            achieved_sigma, achieved_sigma
        )
        band_rows.append(
            {
                "range_lp_mm": [float(low), float(high)],
                "coefficient_count": int(coefficients.shape[0]),
                "maximum_marginal_power_relative_error": float(
                    np.max(
                        np.abs(np.diag(achieved) - np.diag(covariance))
                        / np.maximum(np.diag(covariance), 1e-30)
                    )
                ),
                "maximum_correlation_absolute_error": float(
                    np.max(np.abs(achieved_correlation - target_correlation))
                ),
            }
        )
    candidate = np.fft.irfft2(
        transformed, s=(height, width), axes=(0, 1)
    ).real.astype(np.float32)
    return candidate, {
        "rho": rho,
        "bands": band_rows,
        "maximum_band_marginal_power_relative_error": max(
            row["maximum_marginal_power_relative_error"] for row in band_rows
        ),
        "maximum_band_correlation_absolute_error": max(
            row["maximum_correlation_absolute_error"] for row in band_rows
        ),
    }


def transform_with_48um_closure(
    residual: np.ndarray, rho: float
) -> tuple[np.ndarray, dict[str, object]]:
    candidate, spectral = bandwise_equicorrelation(residual, rho)
    original_48, aperture = filter_48um(residual)
    candidate_48, _ = filter_48um(candidate)
    original_sigma = np.std(original_48, axis=(0, 1), dtype=np.float64)
    candidate_sigma = np.std(candidate_48, axis=(0, 1), dtype=np.float64)
    scale = original_sigma / np.maximum(candidate_sigma, 1e-20)
    original_mean = np.mean(residual, axis=(0, 1), dtype=np.float64)
    candidate_mean = np.mean(candidate, axis=(0, 1), dtype=np.float64)
    closed = (
        original_mean[None, None, :]
        + (candidate - candidate_mean[None, None, :])
        * scale[None, None, :]
    ).astype(np.float32)
    closed_48, _ = filter_48um(closed)
    closed_sigma = np.std(closed_48, axis=(0, 1), dtype=np.float64)
    return closed, {
        "spectral_transform": spectral,
        "aperture": aperture,
        "original_48um": covariance_and_correlation(original_48),
        "preclosure_48um": covariance_and_correlation(candidate_48),
        "closure_scale_rgb": scale.tolist(),
        "closed_48um": covariance_and_correlation(closed_48),
        "maximum_closed_marginal_rms_relative_error": float(
            np.max(np.abs(closed_sigma - original_sigma) / original_sigma)
        ),
        "native": covariance_and_correlation(closed),
    }


def direct_projection(
    engine: Emulsion5279Engine, negative: FormedNegative, frame: int
) -> dict[str, np.ndarray]:
    return render_local_endpoint(engine, negative, frame, 1.0, 1.0)


def current_projection(
    engine: Emulsion5279Engine, negative: FormedNegative, frame: int
) -> dict[str, np.ndarray]:
    local = render_local_endpoint(engine, negative, frame, 0.0, 0.66)
    return publish_policy(
        local,
        {
            "publication": "scan_referenced",
            "publication_hf_retention": 0.0,
        },
    )


def observer_summary(row: dict[str, np.ndarray]) -> dict[str, object]:
    projection_residual = row["projection"] - row["mean_projection"]
    scan_residual = row["scan"] - row["mean_scan"]
    integrated_projection = exact_integer_area(row["projection"], 3)
    integrated_mean = exact_integer_area(row["mean_projection"], 3)
    integrated_residual = integrated_projection - integrated_mean
    native_rms = luma_opponent_rms(projection_residual)
    integrated_rms = luma_opponent_rms(integrated_residual)
    return {
        "projection_grain_rms": native_rms,
        "projection_exact_3x3_retention": {
            key: float(integrated_rms[key] / max(native_rms[key], 1e-20))
            for key in ("rgb", "luma", "opponent")
        },
        "scan_grain_rms": luma_opponent_rms(scan_residual),
        "projection_mean_relative_colour_tail": mean_relative_tail_or_none(
            row["projection"], row["mean_projection"]
        ),
        "scan_mean_relative_colour_tail": mean_relative_tail_or_none(
            row["scan"], row["mean_scan"]
        ),
    }


def audit_field(
    engine: Emulsion5279Engine,
    negative: FormedNegative,
    frame: int,
) -> dict[str, object]:
    residual = (
        negative.formed_record_density - negative.mean_record_density
    ).astype(np.float32)
    rows: dict[str, object] = {
        "original_density_bounds": {
            "minimum_rgb": np.min(
                negative.formed_record_density, axis=(0, 1)
            ).tolist(),
            "below_zero_count": int(
                np.sum(negative.formed_record_density < 0.0)
            ),
        },
        "current_v72_managed": observer_summary(
            current_projection(engine, negative, frame)
        ),
        "direct_unmanaged_original_covariance": observer_summary(
            direct_projection(engine, negative, frame)
        ),
    }
    transformed_rows: dict[str, object] = {}
    for rho in RHO_ENDPOINTS:
        transformed_residual, transform = transform_with_48um_closure(
            residual, rho
        )
        candidate = FormedNegative(
            negative.mean_record_density,
            negative.mean_record_density + transformed_residual,
        )
        formed = candidate.formed_record_density
        transformed_rows[f"rho_{rho:.3f}"] = {
            "transform": transform,
            "density_bounds": {
                "minimum_rgb": np.min(formed, axis=(0, 1)).tolist(),
                "below_zero_count": int(np.sum(formed < 0.0)),
            },
            "observer": observer_summary(
                direct_projection(engine, candidate, frame)
            ),
        }
    rows["equicorrelation_bounds"] = transformed_rows
    return rows


def uniform_negative(log_exposure: float, frame: int) -> FormedNegative:
    height, width = 192, 5760
    records = np.full(
        (height, width, 3), 10.0 ** (log_exposure + 1.0), dtype=np.float32
    )
    log_field = np.full_like(records, log_exposure, dtype=np.float32)
    activations = e.subemulsion_activation_probabilities(log_field)
    mean = e.develop_5279_record_density_from_log_exposure(
        log_field, precomputed_activations=activations
    )
    formed = e.form_5279_multilayer_record_density(
        records,
        frame,
        1.0,
        1,
        precomputed_mean_density=mean,
        precomputed_log_exposure=log_field,
        precomputed_activations=activations,
    )
    return FormedNegative(mean, formed)


def measure(input_path: Path, decoder_path: Path) -> dict[str, object]:
    config = EngineConfig(
        profile="v72",
        exposure_stops=0.45,
        grain_scale=1.0,
        oversample=1,
        mode=EngineMode.PRODUCTION_METAL,
        opencv_threads=8,
        binomial_workers=8,
        numba_threads=8,
        array_workers=8,
        observer_branch_workers=1,
        research_baseline=True,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    try:
        with ProResRawDecoder(decoder_path, input_path, 0, 1) as decoder:
            frame, raw = next(iter(decoder))
        full_negative = engine.form_negative(raw, frame)
        strip_height = 384
        start = (full_negative.mean_record_density.shape[0] - strip_height) // 2
        real_strip = FormedNegative(
            full_negative.mean_record_density[start : start + strip_height],
            full_negative.formed_record_density[start : start + strip_height],
        )
        real = audit_field(engine, real_strip, frame)
        uniform = {
            str(log_exposure): audit_field(
                engine,
                uniform_negative(log_exposure, 8000 + index * 100),
                8000 + index * 100,
            )
            for index, log_exposure in enumerate((-1.0, 0.0))
        }
    finally:
        engine.close()

    real_current = real["current_v72_managed"]
    real_direct = real["direct_unmanaged_original_covariance"]
    real_rho99 = real["equicorrelation_bounds"]["rho_0.990"]
    minus1_current = uniform["-1.0"]["current_v72_managed"]
    minus1_rho99 = uniform["-1.0"]["equicorrelation_bounds"]["rho_0.990"]
    zero_current = uniform["0.0"]["current_v72_managed"]
    zero_rho99 = uniform["0.0"]["equicorrelation_bounds"]["rho_0.990"]
    real_bounds = real["equicorrelation_bounds"]
    current_tail = real_current["projection_mean_relative_colour_tail"]
    direct_tail = real_direct["projection_mean_relative_colour_tail"]
    rho99_tail = real_rho99["observer"][
        "projection_mean_relative_colour_tail"
    ]
    assert isinstance(current_tail, dict)
    assert isinstance(direct_tail, dict)
    assert isinstance(rho99_tail, dict)

    return {
        "audit": "V80 5279 cross-record covariance uncertainty bounds",
        "profile": "V72 evidence-minimal record formation",
        "image_change": "none; second-order mathematical bounds only",
        "input": str(input_path),
        "real_fixture": "T020 centered 5760x384 density strip at native scale",
        "rho_endpoints": list(RHO_ENDPOINTS),
        "frequency_edges_lp_mm": FREQUENCY_EDGES_LP_MM.tolist(),
        "constraints": [
            "same formed V72 density residual before covariance transform",
            "same deterministic mean density",
            "frequency-band target equicorrelation is positive semidefinite",
            "each record is closed back to its original measured 48um RMS",
            "direct unmanaged projection is used only as a diagnostic upper endpoint",
            "no rho is interpreted as a measured 5279 coefficient",
        ],
        "real_T020_strip": real,
        "uniform_log_exposure": uniform,
        "causal_findings": {
            "maximum_48um_marginal_rms_closure_error": float(
                max(
                    row["transform"][
                        "maximum_closed_marginal_rms_relative_error"
                    ]
                    for field in (real, *uniform.values())
                    for row in field["equicorrelation_bounds"].values()
                )
            ),
            "T020_projection_opponent_over_luma": {
                "current_v72_managed": real_current[
                    "projection_grain_rms"
                ]["opponent_over_luma"],
                "direct_original_covariance": real_direct[
                    "projection_grain_rms"
                ]["opponent_over_luma"],
                "rho_0_99_direct": real_rho99["observer"][
                    "projection_grain_rms"
                ]["opponent_over_luma"],
            },
            "T020_isolated_opponent_events_gt_0_08": {
                "current_v72_managed": current_tail[
                    "isolated_gt_0_08_count"
                ],
                "direct_original_covariance": direct_tail[
                    "isolated_gt_0_08_count"
                ],
                "rho_0_99_direct": rho99_tail["isolated_gt_0_08_count"],
            },
            "rho_0_99_luma_rms_over_current": float(
                real_rho99["observer"]["projection_grain_rms"]["luma"]
                / real_current["projection_grain_rms"]["luma"]
            ),
            "rho_0_99_opponent_rms_over_current": float(
                real_rho99["observer"]["projection_grain_rms"]["opponent"]
                / real_current["projection_grain_rms"]["opponent"]
            ),
            "every_real_transform_violates_nonnegative_density": bool(
                all(
                    row["density_bounds"]["below_zero_count"] > 0
                    for row in real_bounds.values()
                )
            ),
            "constant_rho_0_99_exposure_mismatch": {
                "logE_minus1_current_opponent_over_luma": (
                    minus1_current["projection_grain_rms"][
                        "opponent_over_luma"
                    ]
                ),
                "logE_minus1_rho_opponent_over_luma": (
                    minus1_rho99["observer"]["projection_grain_rms"][
                        "opponent_over_luma"
                    ]
                ),
                "logE_zero_current_opponent_over_luma": (
                    zero_current["projection_grain_rms"][
                        "opponent_over_luma"
                    ]
                ),
                "logE_zero_rho_opponent_over_luma": (
                    zero_rho99["observer"]["projection_grain_rms"][
                        "opponent_over_luma"
                    ]
                ),
            },
        },
        "evidence_boundary": (
            "This operation preserves second-order marginal amplitude but not "
            "finite-site identities, local exposure-dependent covariance or "
            "higher-order layer statistics. It can locate the missing "
            "observable and reject impossible interpretations; it cannot be "
            "promoted as an emulsion model."
        ),
        "decision": (
            "Reject post-formation linear covariance mixing as the next image "
            "model. Even extreme correlation can approach one aggregate "
            "opponent/luma ratio while changing luma amplitude, failing across "
            "exposures, retaining severe nonlinear colour tails and violating "
            "the finite nonnegative density boundary. Any future physical "
            "candidate must create level-, frequency- and population-dependent "
            "shared finite events during activation/development, preserve "
            "higher-order tails and remain bounded before dye density exists."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode")
    )
    args = parser.parse_args()
    report = measure(args.input, args.decoder)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
