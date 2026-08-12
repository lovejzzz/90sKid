#!/usr/bin/env python3
"""Characterize V45's unmeasured 5279 spatial, colour and temporal structure.

Kodak's public 48-micrometre diffuse-RMS curves constrain marginal density
amplitude after aperture averaging.  They do not identify a spatial NPS,
cross-record covariance, higher-order distribution or temporal correlation.
This audit therefore separates two kinds of result:

* contract gates test only properties that follow from the stated model
  (fresh emulsion per frame, numerical isotropy and absence of clipping);
* descriptive measurements record the current inferred morphology without
  pretending that it is a measured 5279 target.

No image-formation parameter is fitted or changed here.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from types import ModuleType

import numpy as np

import emulsion_experiment as emulsion
import v45_profile
import v48_profile
import v49_profile
import v50_profile
import v51_profile
import v52_profile
import v53_profile
import v54_profile
import v55_profile
import v56_profile
import v57_profile
import v58_profile
import v59_profile
import v60_profile


PROFILES = {
    "v45": v45_profile,
    "v48": v48_profile,
    "v49": v49_profile,
    "v50": v50_profile,
    "v51": v51_profile,
    "v52": v52_profile,
    "v53": v53_profile,
    "v54": v54_profile,
    "v55": v55_profile,
    "v56": v56_profile,
    "v57": v57_profile,
    "v58": v58_profile,
    "v59": v59_profile,
    "v60": v60_profile,
}


DEFAULT_LOG_EXPOSURES = (-3.0, -2.5, -1.0, 0.0)
NPS_EDGES_CYCLES_PER_PIXEL = np.asarray(
    [0.0, 0.03125, 0.0625, 0.125, 0.25, 0.375, 0.5, math.sqrt(0.5)],
    dtype=np.float64,
)


def correlation(first: np.ndarray, second: np.ndarray) -> float:
    a = np.asarray(first, dtype=np.float64).ravel()
    b = np.asarray(second, dtype=np.float64).ravel()
    a -= float(a.mean())
    b -= float(b.mean())
    denominator = math.sqrt(float(np.dot(a, a) * np.dot(b, b)))
    return float(np.dot(a, b) / denominator) if denominator > 0.0 else 0.0


def standardized_moments(values: np.ndarray) -> dict[str, float | list[float]]:
    array = np.asarray(values, dtype=np.float64)
    array -= float(array.mean())
    sigma = max(float(array.std()), 1.0e-30)
    standardized = array / sigma
    return {
        "skewness": float(np.mean(standardized**3)),
        "excess_kurtosis": float(np.mean(standardized**4) - 3.0),
        "standardized_percentiles": np.percentile(
            standardized, [0.1, 1.0, 50.0, 99.0, 99.9]
        ).tolist(),
    }


def spectrum_metrics(sequence: np.ndarray, pixels_per_mm: float) -> dict[str, object]:
    frames, height, width, records = sequence.shape
    window = np.outer(np.hanning(height), np.hanning(width)).astype(np.float64)
    window_energy = float(np.sum(window * window))
    fy = np.fft.fftfreq(height)[:, None]
    fx = np.fft.rfftfreq(width)[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    angle = np.mod(np.arctan2(fy, fx), math.pi)
    radial_band_centres_lp_mm = (
        0.5
        * (NPS_EDGES_CYCLES_PER_PIXEL[:-1] + NPS_EDGES_CYCLES_PER_PIXEL[1:])
        * pixels_per_mm
    )
    angular_edges = np.linspace(0.0, math.pi, 13)

    normalized_bands: list[list[float]] = []
    angular_sector_power_db: list[list[float]] = []
    angular_peak_to_valley_db: list[float] = []
    for record in range(records):
        power = np.zeros((height, width // 2 + 1), dtype=np.float64)
        for frame in range(frames):
            plane = np.asarray(sequence[frame, ..., record], dtype=np.float64)
            plane -= float(plane.mean())
            transformed = np.fft.rfft2(plane * window)
            power += np.abs(transformed) ** 2 / max(window_energy, 1.0e-30)
        power /= float(frames)

        bands = np.asarray(
            [
                float(np.sum(power[(radius >= low) & (radius < high)]))
                for low, high in zip(
                    NPS_EDGES_CYCLES_PER_PIXEL[:-1],
                    NPS_EDGES_CYCLES_PER_PIXEL[1:],
                    strict=True,
                )
            ],
            dtype=np.float64,
        )
        bands /= max(float(bands.sum()), 1.0e-30)
        normalized_bands.append(bands.tolist())

        # Ignore the DC neighborhood and the corner-only frequencies. Equal-
        # angle sector means are a sensitive detector for raster axes or a
        # rotating kernel pattern in an otherwise uniform patch.
        annulus = (radius >= 0.04) & (radius < 0.45)
        sectors = []
        for low, high in zip(angular_edges[:-1], angular_edges[1:], strict=True):
            mask = annulus & (angle >= low) & (angle < high)
            sectors.append(float(np.mean(power[mask])))
        sector_array = np.asarray(sectors, dtype=np.float64)
        sector_db = 10.0 * np.log10(
            np.maximum(sector_array, 1.0e-30)
            / max(float(np.mean(sector_array)), 1.0e-30)
        )
        angular_sector_power_db.append(sector_db.tolist())
        angular_peak_to_valley_db.append(float(np.ptp(sector_db)))

    return {
        "nps_band_edges_cycles_per_pixel": NPS_EDGES_CYCLES_PER_PIXEL.tolist(),
        "nps_band_centres_line_pairs_per_mm": radial_band_centres_lp_mm.tolist(),
        "normalized_nps_bands_records": normalized_bands,
        "angular_sector_power_db_records": angular_sector_power_db,
        "angular_peak_to_valley_db_records": angular_peak_to_valley_db,
    }


def measure_exposure(
    *,
    width: int,
    height: int,
    frames: int,
    log_exposure: float,
    first_frame_identity: int,
) -> dict[str, object]:
    level = np.float32(10.0 ** (log_exposure + 1.0))
    records = np.full((height, width, 3), level, dtype=np.float32)
    log_exposure_field = np.full_like(records, log_exposure, dtype=np.float32)
    activations = emulsion.subemulsion_activation_probabilities(log_exposure_field)
    mean = emulsion.develop_5279_record_density_from_log_exposure(
        log_exposure_field,
        precomputed_activations=activations,
    )

    margin = 24
    residual_frames = []
    bound_point_mass_fractions = []
    above_legacy_upper_fractions = []
    upper = emulsion.SENSITO_DENSITY_RGB[:, -1] + 0.12
    for offset in range(frames):
        formed = emulsion.form_5279_multilayer_record_density(
            records,
            first_frame_identity + offset,
            1.0,
            1,
            precomputed_mean_density=mean,
            precomputed_log_exposure=log_exposure_field,
            precomputed_activations=activations,
        )
        residual_frames.append(
            (formed - mean)[margin:-margin, margin:-margin].astype(np.float32)
        )
        if (
            emulsion.GRAIN_LOCAL_DENSITY_BOUND_MODE
            == "legacy_macro_dmax_plus_0_12"
        ):
            at_bound = (formed <= 0.0) | (formed >= upper[None, None, :])
        else:
            at_bound = formed <= 0.0
        bound_point_mass_fractions.append(np.mean(at_bound, axis=(0, 1)))
        above_legacy_upper_fractions.append(
            np.mean(formed >= upper[None, None, :], axis=(0, 1))
        )

    sequence = np.stack(residual_frames)
    sequence -= sequence.mean(axis=(1, 2), keepdims=True)
    rms = np.sqrt(np.mean(sequence * sequence, axis=(0, 1, 2)))
    temporal_difference_rms = np.sqrt(
        np.mean(np.diff(sequence, axis=0) ** 2, axis=(0, 1, 2))
    )
    temporal_ratio = temporal_difference_rms / np.maximum(
        math.sqrt(2.0) * rms, 1.0e-30
    )

    temporal_correlations = [
        correlation(sequence[:-1, ..., record], sequence[1:, ..., record])
        for record in range(3)
    ]
    x_lag = [
        correlation(sequence[..., record][:, :, :-1], sequence[..., record][:, :, 1:])
        for record in range(3)
    ]
    y_lag = [
        correlation(sequence[..., record][:, :-1, :], sequence[..., record][:, 1:, :])
        for record in range(3)
    ]

    flattened = sequence.transpose(3, 0, 1, 2).reshape(3, -1)
    cross_record_correlation = np.corrcoef(flattened)
    cross_record_covariance = np.cov(flattened)
    covariance_eigenvalues = np.linalg.eigvalsh(cross_record_covariance)

    return {
        "log_exposure": log_exposure,
        "frames": frames,
        "unfiltered_density_rms_records": rms.tolist(),
        "temporal_difference_rms_records": temporal_difference_rms.tolist(),
        "temporal_difference_over_independent_expectation_records": (
            temporal_ratio.tolist()
        ),
        "temporal_lag1_correlation_records": temporal_correlations,
        "spatial_x_lag1_correlation_records": x_lag,
        "spatial_y_lag1_correlation_records": y_lag,
        "spatial_lag1_anisotropy_records": np.abs(
            np.asarray(x_lag) - np.asarray(y_lag)
        ).tolist(),
        "cross_record_correlation": cross_record_correlation.tolist(),
        "cross_record_covariance_eigenvalues": covariance_eigenvalues.tolist(),
        "maximum_numerical_bound_point_mass_fraction_records": np.max(
            bound_point_mass_fractions, axis=0
        ).tolist(),
        "maximum_fraction_above_legacy_macro_guard_records": np.max(
            above_legacy_upper_fractions, axis=0
        ).tolist(),
        "higher_order_records": [
            standardized_moments(flattened[record]) for record in range(3)
        ],
        "spectrum": spectrum_metrics(sequence, width / 24.9),
    }


def measure(
    *,
    width: int,
    height: int,
    frames: int,
    log_exposures: tuple[float, ...],
    first_frame_identity: int,
    profile_module: ModuleType = v45_profile,
) -> dict[str, object]:
    if width < 1800:
        raise ValueError("width must be at least 1800 to preserve 35 mm scale")
    if height < 192:
        raise ValueError("height must be at least 192 for stable statistics")
    if frames < 4:
        raise ValueError("at least four frames are required for a temporal audit")

    profile_module.apply(emulsion)
    emulsion.BINOMIAL_SAMPLER_MODE = "striped_v25"
    emulsion.BINOMIAL_PARALLEL_WORKERS = 4

    rows = [
        measure_exposure(
            width=width,
            height=height,
            frames=frames,
            log_exposure=log_exposure,
            first_frame_identity=first_frame_identity + 100 * index,
        )
        for index, log_exposure in enumerate(log_exposures)
    ]
    max_temporal_correlation = max(
        abs(value)
        for row in rows
        for value in row["temporal_lag1_correlation_records"]  # type: ignore[index]
    )
    max_temporal_ratio_error = max(
        abs(value - 1.0)
        for row in rows
        for value in row[
            "temporal_difference_over_independent_expectation_records"
        ]  # type: ignore[index]
    )
    max_lag_anisotropy = max(
        value
        for row in rows
        for value in row["spatial_lag1_anisotropy_records"]  # type: ignore[index]
    )
    max_bound_point_mass_fraction = max(
        value
        for row in rows
        for value in row[
            "maximum_numerical_bound_point_mass_fraction_records"
        ]  # type: ignore[index]
    )
    min_covariance_eigenvalue = min(
        value
        for row in rows
        for value in row["cross_record_covariance_eigenvalues"]  # type: ignore[index]
    )
    gates = {
        "maximum_absolute_temporal_lag1_correlation": {
            "value": max_temporal_correlation,
            "limit": 0.03,
            "pass": max_temporal_correlation <= 0.03,
        },
        "maximum_temporal_difference_ratio_error": {
            "value": max_temporal_ratio_error,
            "limit": 0.03,
            "pass": max_temporal_ratio_error <= 0.03,
        },
        "maximum_spatial_lag1_anisotropy": {
            "value": max_lag_anisotropy,
            "limit": 0.03,
            "pass": max_lag_anisotropy <= 0.03,
        },
        "maximum_numerical_bound_point_mass_fraction": {
            "value": max_bound_point_mass_fraction,
            "limit": 1.0e-6,
            "pass": max_bound_point_mass_fraction <= 1.0e-6,
        },
        "minimum_cross_record_covariance_eigenvalue": {
            "value": min_covariance_eigenvalue,
            "limit": -1.0e-12,
            "pass": min_covariance_eigenvalue >= -1.0e-12,
        },
    }
    return {
        "audit": "V47 5279 spatial/cross-record/temporal structure",
        "image_change": "none",
        "profile": profile_module.PROFILE["name"],
        "fixture": {
            "width": width,
            "height": height,
            "interior_width": width - 48,
            "interior_height": height - 48,
            "assumed_35mm_image_width_mm": 24.9,
            "pixels_per_mm": width / 24.9,
            "frames_per_exposure": frames,
            "sampler": "striped_v25 binomial CPU; statistical audit",
        },
        "rows": rows,
        "contract_gates": gates,
        "pass": all(bool(gate["pass"]) for gate in gates.values()),
        "evidence_boundary": {
            "gated": (
                "fresh-frame independence, numerical isotropy, covariance "
                "validity and absence of a numerical density-bound point mass"
            ),
            "descriptive_only": (
                "NPS shape, higher-order tails and cross-record correlation; "
                "no public stock-specific target identifies these quantities"
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=384)
    parser.add_argument("--frames", type=int, default=6)
    parser.add_argument(
        "--log-exposures",
        type=float,
        nargs="+",
        default=list(DEFAULT_LOG_EXPOSURES),
    )
    parser.add_argument("--first-frame-identity", type=int, default=4700)
    parser.add_argument("--profile", choices=tuple(PROFILES), default="v45")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = measure(
        width=args.width,
        height=args.height,
        frames=args.frames,
        log_exposures=tuple(args.log_exposures),
        first_frame_identity=args.first_frame_identity,
        profile_module=PROFILES[args.profile],
    )
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
