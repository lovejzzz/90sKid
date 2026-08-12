#!/usr/bin/env python3
"""Validate 5279 diffuse RMS at Kodak's physical 48-micrometre aperture.

The historical V39 gate measured the unfiltered pixel standard deviation on a
320-pixel-wide fixture.  At that scale the nominal 48 um aperture rasterizes to
one pixel, so the test did not exercise the published measurement.  This audit
uses a scale large enough for a non-degenerate circular aperture, filters the
formed record density with that aperture, and compares the observed standard
deviation with the digitized Kodak curves over the complete modeled exposure
range.

This is a conformance audit of the existing V45/V42 negative.  It does not fit
or change any image-formation parameter.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import ModuleType

import cv2
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
import v72_profile


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
    "v72": v72_profile,
}


DEFAULT_LOG_EXPOSURES = (
    -4.0,
    -3.5,
    -3.0,
    -2.5,
    -2.0,
    -1.5,
    -1.0,
    -0.5,
    0.0,
    1.0,
)


def measure(
    *,
    width: int,
    height: int,
    log_exposures: tuple[float, ...],
    first_frame_identity: int,
    tolerance: float,
    profile_module: ModuleType = v45_profile,
    stochastic_exposure_policy: str | None = None,
) -> dict[str, object]:
    if width < 1800:
        raise ValueError(
            "width must be at least 1800 so the 48 um aperture has useful "
            "raster support"
        )
    if height < 192:
        raise ValueError("height must be at least 192 for stable patch statistics")

    profile_module.apply(emulsion)
    if stochastic_exposure_policy is not None:
        emulsion.GRAIN_STOCHASTIC_EXPOSURE_POLICY = stochastic_exposure_policy
    # A striped CPU sampler reduces peak allocation while preserving the exact
    # binomial distribution and absolute-frame seed contract.  This audit tests
    # statistics, not identity with one historical random realization.
    emulsion.BINOMIAL_SAMPLER_MODE = "striped_v25"
    emulsion.BINOMIAL_PARALLEL_WORKERS = 4

    aperture_radius = (
        0.5
        * emulsion.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
        * 1e-3
        * (width / 24.9)
    )
    aperture = emulsion.disk_kernel(aperture_radius)
    aperture /= float(aperture.sum())
    if int(np.count_nonzero(aperture)) < 9:
        raise ValueError("48 um aperture rasterization is still degenerate")

    margin = max(24, aperture.shape[0] * 4)
    rows: list[dict[str, object]] = []
    for index, log_exposure in enumerate(log_exposures):
        # develop_5279_record_density uses log10(records)-1 as stock log E.
        record_level = np.float32(10.0 ** (log_exposure + 1.0))
        records = np.full((height, width, 3), record_level, dtype=np.float32)
        mean_density = emulsion.develop_5279_record_density(records)
        formed_density = emulsion.form_5279_multilayer_record_density(
            records,
            first_frame_identity + index,
            1.0,
            1,
            precomputed_mean_density=mean_density,
        )
        residual = formed_density - mean_density
        observed = np.stack(
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
        )
        interior = np.s_[margin:-margin, margin:-margin]
        raw_sigma = np.std(residual[interior], axis=(0, 1)).astype(np.float64)
        aperture_sigma = np.std(observed[interior], axis=(0, 1)).astype(np.float64)
        target_sigma = emulsion.published_5279_granularity_sigma(
            np.full((1, 1, 3), log_exposure, dtype=np.float32)
        )[0, 0].astype(np.float64)
        relative_error = (aperture_sigma - target_sigma) / target_sigma
        rows.append(
            {
                "log_exposure": log_exposure,
                "target_sigma_d_rgb": target_sigma.tolist(),
                "measured_48um_sigma_d_rgb": aperture_sigma.tolist(),
                "relative_error_rgb": relative_error.tolist(),
                "unfiltered_pixel_sigma_d_rgb": raw_sigma.tolist(),
                "unfiltered_to_48um_ratio_rgb": (
                    raw_sigma / aperture_sigma
                ).tolist(),
            }
        )

    worst = max(
        abs(float(value))
        for row in rows
        for value in row["relative_error_rgb"]  # type: ignore[index]
    )
    return {
        "audit": "V46 5279 physical 48-micrometre diffuse RMS",
        "image_change": "none",
        "profile": profile_module.PROFILE["name"],
        "stochastic_exposure_policy": (
            emulsion.GRAIN_STOCHASTIC_EXPOSURE_POLICY
        ),
        "fixture": {
            "width": width,
            "height": height,
            "assumed_35mm_image_width_mm": 24.9,
            "aperture_diameter_um": (
                emulsion.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
            ),
            "aperture_radius_pixels": aperture_radius,
            "aperture_kernel_shape": list(aperture.shape),
            "aperture_nonzero_samples": int(np.count_nonzero(aperture)),
            "excluded_border_pixels": margin,
            "sampler": "striped_v25 binomial CPU; statistical audit",
        },
        "rows": rows,
        "gate": {
            "maximum_absolute_relative_error": worst,
            "tolerance": tolerance,
            "pass": worst <= tolerance,
        },
        "interpretation": (
            "A pass validates the implemented aperture-weighted marginal RMS "
            "only. It does not identify 5279's NPS, cross-record covariance, "
            "fast/medium/slow coating recipe, or DIR coefficients."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=384)
    parser.add_argument(
        "--log-exposures",
        type=float,
        nargs="+",
        default=list(DEFAULT_LOG_EXPOSURES),
    )
    parser.add_argument("--first-frame-identity", type=int, default=1200)
    parser.add_argument("--tolerance", type=float, default=0.02)
    parser.add_argument("--profile", choices=tuple(PROFILES), default="v45")
    parser.add_argument(
        "--stochastic-exposure-policy",
        choices=(
            "legacy_target_only_endpoint_hold",
            "full_stochastic_state_endpoint_hold",
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = measure(
        width=args.width,
        height=args.height,
        log_exposures=tuple(args.log_exposures),
        first_frame_identity=args.first_frame_identity,
        tolerance=args.tolerance,
        profile_module=PROFILES[args.profile],
        stochastic_exposure_policy=args.stochastic_exposure_policy,
    )
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if not report["gate"]["pass"]:  # type: ignore[index]
        raise SystemExit(1)


if __name__ == "__main__":
    main()
