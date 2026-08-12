#!/usr/bin/env python3
"""Audit the unmeasured joint colour statistics of the V66 5279 model.

Kodak publishes marginal diffuse-RMS granularity for the red-, green- and
blue-sensitive records through a 48 um aperture.  Those three curves do not
identify their joint covariance.  This audit therefore measures the covariance
that the present model *predicts*, traces it through the negative MTF, the
Spirit/Cineon data coordinate and the two named Blu-ray viewing treatments,
and isolates the contributions of two explicitly unmeasured priors:

* speed-population dye-record mixing; and
* stochastic DIR/interimage transport.

Nothing in this file fits or changes a production profile.  Its results are
descriptive until a calibrated 5279 uniform-field scan supplies a target.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import time

import cv2
import numpy as np

import emulsion_experiment as emulsion
import v66_profile


DEFAULT_LOG_EXPOSURES = (-3.0, -2.5, -1.0, 0.0)

# Orthonormal common/opponent basis.  Energy is preserved, so the common and
# opponent variance fractions are comparable across record-density and display
# stages without silently privileging one RGB luma convention.
COMMON_OPPONENT_BASIS = np.asarray(
    [
        [1.0, 1.0, 1.0],
        [1.0, -1.0, 0.0],
        [1.0, 1.0, -2.0],
    ],
    dtype=np.float64,
)
COMMON_OPPONENT_BASIS[0] /= np.sqrt(3.0)
COMMON_OPPONENT_BASIS[1] /= np.sqrt(2.0)
COMMON_OPPONENT_BASIS[2] /= np.sqrt(6.0)


def identity_population_mix() -> np.ndarray:
    identity = np.eye(3, dtype=np.float32)
    return np.repeat(identity[None, ...], 3, axis=0)


@contextmanager
def structural_priors(*, record_mix: bool, stochastic_dir: bool):
    original_mix = emulsion.SUBEMULSION_DYE_RECORD_MIX.copy()
    original_dir_scale = float(emulsion.DIR_STOCHASTIC_COUPLING_SCALE)
    try:
        if not record_mix:
            emulsion.SUBEMULSION_DYE_RECORD_MIX = identity_population_mix()
        if not stochastic_dir:
            emulsion.DIR_STOCHASTIC_COUPLING_SCALE = 0.0
        yield
    finally:
        emulsion.SUBEMULSION_DYE_RECORD_MIX = original_mix
        emulsion.DIR_STOCHASTIC_COUPLING_SCALE = original_dir_scale


def covariance_metrics(sequence: np.ndarray) -> dict[str, object]:
    """Summarize one [frame, y, x, RGB] zero-mean stochastic sequence."""
    values = np.asarray(sequence, dtype=np.float64)
    values -= values.mean(axis=(1, 2), keepdims=True)
    flat = values.reshape(-1, 3)
    covariance = np.cov(flat, rowvar=False)
    sigma = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    denominator = np.outer(sigma, sigma)
    correlation = np.divide(
        covariance,
        denominator,
        out=np.zeros_like(covariance),
        where=denominator > 0.0,
    )
    transformed_covariance = (
        COMMON_OPPONENT_BASIS @ covariance @ COMMON_OPPONENT_BASIS.T
    )
    total_variance = max(float(np.trace(transformed_covariance)), 1.0e-30)
    eigenvalues = np.linalg.eigvalsh(covariance)
    return {
        "sigma_rgb": sigma.tolist(),
        "covariance_rgb": covariance.tolist(),
        "correlation_rgb": correlation.tolist(),
        "covariance_eigenvalues": eigenvalues.tolist(),
        "common_opponent_covariance": transformed_covariance.tolist(),
        "common_variance_fraction": (
            float(transformed_covariance[0, 0]) / total_variance
        ),
        "opponent_variance_fraction": (
            float(transformed_covariance[1, 1] + transformed_covariance[2, 2])
            / total_variance
        ),
        "largest_eigenvalue_fraction": float(eigenvalues[-1])
        / max(float(np.sum(eigenvalues)), 1.0e-30),
    }


def filter_48um(residual: np.ndarray, aperture: np.ndarray) -> np.ndarray:
    return np.stack(
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


def legacy_managed_bluray(
    formed_open: np.ndarray,
    mean_open: np.ndarray,
) -> np.ndarray:
    formed_finish = emulsion.finish_cineon_scan_for_bluray(formed_open)
    mean_finish = emulsion.finish_cineon_scan_for_bluray(mean_open)
    managed = mean_finish + emulsion.finish_bluray_grain_delta(
        mean_finish, formed_finish - mean_finish
    )
    managed = emulsion.compress_oklab_chroma_to_rec709(managed)
    if emulsion.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED:
        managed = emulsion.neutralize_spirit_finished_gray_scale(managed)
    return np.clip(managed, 0.0, 1.0).astype(np.float32)


def pointwise_bluray(cineon_code: np.ndarray) -> np.ndarray:
    opened = emulsion.render_cineon_open_display_from_code(cineon_code)
    finished = emulsion.finish_cineon_scan_for_bluray(opened)
    finished = emulsion.compress_oklab_chroma_to_rec709(finished)
    if emulsion.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED:
        finished = emulsion.neutralize_spirit_finished_gray_scale(finished)
    return np.clip(finished, 0.0, 1.0).astype(np.float32)


def measure_condition_exposure(
    *,
    width: int,
    height: int,
    frames: int,
    log_exposure: float,
    first_frame_identity: int,
    aperture: np.ndarray,
    margin: int,
) -> dict[str, object]:
    level = np.float32(10.0 ** (log_exposure + 1.0))
    records = np.full((height, width, 3), level, dtype=np.float32)
    log_field = np.full_like(records, log_exposure, dtype=np.float32)
    activations = emulsion.subemulsion_activation_probabilities(log_field)
    mean = emulsion.develop_5279_record_density_from_log_exposure(
        log_field, precomputed_activations=activations
    )
    negative_mean = emulsion.apply_5279_mtf_to_record_density(mean, 1.0)
    scanner_mean = emulsion.apply_spirit_2k_scan_aperture_to_density(
        emulsion.scanner_density_from_total_record_density(negative_mean)
    )
    code_mean = emulsion.quantized_cineon_code_from_scanner_density(scanner_mean)
    open_mean = emulsion.render_cineon_open_display_from_code(code_mean)
    pointwise_mean = pointwise_bluray(code_mean)

    stages: dict[str, list[np.ndarray]] = {
        "formed_density_48um": [],
        "processed_negative_after_mtf": [],
        "cineon_printing_density_code": [],
        "cineon_pointwise_bluray": [],
        "legacy_managed_bluray": [],
    }
    for offset in range(frames):
        formed = emulsion.form_5279_multilayer_record_density(
            records,
            first_frame_identity + offset,
            1.0,
            1,
            precomputed_mean_density=mean,
            precomputed_log_exposure=log_field,
            precomputed_activations=activations,
        )
        formed_residual = formed - mean
        negative_formed = (negative_mean + formed_residual).astype(np.float32)
        scanner_formed = emulsion.apply_spirit_2k_scan_aperture_to_density(
            emulsion.scanner_density_from_total_record_density(negative_formed)
        )
        code_formed = emulsion.quantized_cineon_code_from_scanner_density(
            scanner_formed
        )
        open_formed = emulsion.render_cineon_open_display_from_code(code_formed)
        pointwise_formed = pointwise_bluray(code_formed)
        legacy_formed = legacy_managed_bluray(open_formed, open_mean)

        interior = np.s_[margin:-margin, margin:-margin]
        stages["formed_density_48um"].append(
            filter_48um(formed_residual, aperture)[interior]
        )
        stages["processed_negative_after_mtf"].append(
            (negative_formed - negative_mean)[interior]
        )
        stages["cineon_printing_density_code"].append(
            (code_formed.astype(np.float32) - code_mean.astype(np.float32))[interior]
        )
        stages["cineon_pointwise_bluray"].append(
            (pointwise_formed - pointwise_mean)[interior]
        )
        # The legacy result has the same deterministic finish as pointwise at a
        # uniform field; subtracting pointwise_mean therefore isolates only its
        # historical mean-relative grain-management operation.
        stages["legacy_managed_bluray"].append(
            (legacy_formed - pointwise_mean)[interior]
        )

    target_sigma = emulsion.published_5279_granularity_sigma(
        np.full((1, 1, 3), log_exposure, dtype=np.float32)
    )[0, 0]
    summaries = {
        name: covariance_metrics(np.stack(values))
        for name, values in stages.items()
    }
    observed_sigma = np.asarray(
        summaries["formed_density_48um"]["sigma_rgb"], dtype=np.float64
    )
    return {
        "log_exposure": log_exposure,
        "published_48um_sigma_d_rgb": target_sigma.tolist(),
        "measured_48um_relative_error_rgb": (
            (observed_sigma - target_sigma) / np.maximum(target_sigma, 1.0e-12)
        ).tolist(),
        "stages": summaries,
    }


def theoretical_endpoints(sigma: np.ndarray) -> dict[str, object]:
    sigma = np.asarray(sigma, dtype=np.float64)
    independent = np.diag(sigma * sigma)
    common = np.outer(sigma, sigma)

    def summarize(covariance: np.ndarray) -> dict[str, object]:
        # covariance_metrics expects samples; summarize the covariance directly
        # here to avoid adding Monte Carlo noise to analytic endpoints.
        transformed = COMMON_OPPONENT_BASIS @ covariance @ COMMON_OPPONENT_BASIS.T
        total = max(float(np.trace(transformed)), 1.0e-30)
        eigenvalues = np.linalg.eigvalsh(covariance)
        denominator = np.outer(sigma, sigma)
        correlation = np.divide(
            covariance,
            denominator,
            out=np.zeros_like(covariance),
            where=denominator > 0.0,
        )
        return {
            "covariance_rgb": covariance.tolist(),
            "correlation_rgb": correlation.tolist(),
            "covariance_eigenvalues": eigenvalues.tolist(),
            "common_variance_fraction": float(transformed[0, 0]) / total,
            "opponent_variance_fraction": (
                float(transformed[1, 1] + transformed[2, 2]) / total
            ),
            "largest_eigenvalue_fraction": float(eigenvalues[-1])
            / max(float(np.sum(eigenvalues)), 1.0e-30),
        }

    return {
        "independent_records_same_marginals": summarize(independent),
        "perfect_common_mode_same_marginals": summarize(common),
    }


def measure(
    *,
    width: int,
    height: int,
    frames: int,
    log_exposures: tuple[float, ...],
    first_frame_identity: int,
) -> dict[str, object]:
    if width < 1800:
        raise ValueError("width must be at least 1800 to preserve 35 mm scale")
    if height < 192:
        raise ValueError("height must be at least 192 for stable statistics")
    if frames < 4:
        raise ValueError("at least four realizations are required")

    v66_profile.apply(emulsion)
    emulsion.BINOMIAL_SAMPLER_MODE = "striped_v25"
    emulsion.BINOMIAL_PARALLEL_WORKERS = 4

    aperture_radius = (
        0.5
        * emulsion.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
        * 1.0e-3
        * (width / 24.9)
    )
    aperture = emulsion.disk_kernel(aperture_radius)
    aperture /= float(aperture.sum())
    margin = max(32, aperture.shape[0] * 4)

    conditions = {
        "current_mix_and_stochastic_dir": (True, True),
        "record_mix_only_no_stochastic_dir": (True, False),
        "stochastic_dir_only_identity_record_mix": (False, True),
        "independent_records_no_mix_no_stochastic_dir": (False, False),
    }
    started = time.perf_counter()
    condition_rows: dict[str, list[dict[str, object]]] = {}
    for name, (use_mix, use_dir) in conditions.items():
        rows = []
        with structural_priors(record_mix=use_mix, stochastic_dir=use_dir):
            for exposure_index, log_exposure in enumerate(log_exposures):
                rows.append(
                    measure_condition_exposure(
                        width=width,
                        height=height,
                        frames=frames,
                        log_exposure=log_exposure,
                        first_frame_identity=(
                            first_frame_identity
                            + exposure_index * 100
                        ),
                        aperture=aperture,
                        margin=margin,
                    )
                )
        condition_rows[name] = rows

    endpoints = {}
    for log_exposure in log_exposures:
        sigma = emulsion.published_5279_granularity_sigma(
            np.full((1, 1, 3), log_exposure, dtype=np.float32)
        )[0, 0]
        endpoints[str(log_exposure)] = theoretical_endpoints(sigma)

    current_rows = condition_rows["current_mix_and_stochastic_dir"]
    worst_rms_error = max(
        abs(float(value))
        for row in current_rows
        for value in row["measured_48um_relative_error_rgb"]  # type: ignore[index]
    )
    return {
        "audit": "V70 5279 joint colour covariance ownership",
        "profile": v66_profile.PROFILE["name"],
        "image_change": "none",
        "elapsed_seconds": time.perf_counter() - started,
        "fixture": {
            "width": width,
            "height": height,
            "frames_per_exposure": frames,
            "log_exposures": list(log_exposures),
            "assumed_35mm_image_width_mm": 24.9,
            "aperture_diameter_um": (
                emulsion.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
            ),
            "aperture_radius_pixels": aperture_radius,
            "excluded_border_pixels": margin,
            "sampler": "striped_v25 binomial CPU; statistical audit",
            "common_opponent_basis_rows": COMMON_OPPONENT_BASIS.tolist(),
        },
        "conditions": condition_rows,
        "analytic_same_marginal_endpoints": endpoints,
        "gates": {
            "current_profile_maximum_48um_rms_relative_error": {
                "value": worst_rms_error,
                "limit": 0.02,
                "pass": worst_rms_error <= 0.02,
            },
            "all_covariances_positive_semidefinite": {
                "pass": all(
                    min(
                        row["stages"][stage]["covariance_eigenvalues"]  # type: ignore[index]
                    )
                    >= -1.0e-12
                    for rows in condition_rows.values()
                    for row in rows
                    for stage in row["stages"]  # type: ignore[index]
                )
            },
        },
        "evidence_boundary": {
            "measured": (
                "Kodak's marginal per-record 48 um diffuse-RMS curves"
            ),
            "descriptive_only": (
                "all cross-record covariance, common/opponent allocation, "
                "NPS and display-stage colour-grain results"
            ),
            "production_decision": (
                "No covariance prior may be promoted from this audit alone."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=256)
    parser.add_argument("--frames", type=int, default=4)
    parser.add_argument(
        "--log-exposures",
        type=float,
        nargs="+",
        default=list(DEFAULT_LOG_EXPOSURES),
    )
    parser.add_argument("--first-frame-identity", type=int, default=7000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = measure(
        width=args.width,
        height=args.height,
        frames=args.frames,
        log_exposures=tuple(args.log_exposures),
        first_frame_identity=args.first_frame_identity,
    )
    payload = json.dumps(result, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if not all(bool(gate["pass"]) for gate in result["gates"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
