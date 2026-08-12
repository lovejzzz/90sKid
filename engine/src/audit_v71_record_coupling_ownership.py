#!/usr/bin/env python3
"""Separate 5279 record sensitivity, direct record mix, DIR and dye spectra.

This is a deterministic separation-wedge/Jacobian audit.  It asks whether the
unmeasured SUBEMULSION_DYE_RECORD_MIX operator owns a distinct observable or
duplicates mechanisms already represented by spectral sensitivity, net dye
spectra/masking and development-inhibitor transport.  No production constant
is fitted or changed.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as emulsion
import v66_profile


DEFAULT_LOG_EXPOSURES = (-3.0, -2.5, -1.0, 0.0)


def identity_population_mix() -> np.ndarray:
    return np.repeat(np.eye(3, dtype=np.float32)[None, ...], 3, axis=0)


@contextmanager
def deterministic_coupling(*, record_mix: bool, interimage_dir: bool):
    original_mix = emulsion.SUBEMULSION_DYE_RECORD_MIX.copy()
    original_dir = float(emulsion.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH)
    try:
        if not record_mix:
            emulsion.SUBEMULSION_DYE_RECORD_MIX = identity_population_mix()
        if not interimage_dir:
            emulsion.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH = 0.0
        yield
    finally:
        emulsion.SUBEMULSION_DYE_RECORD_MIX = original_mix
        emulsion.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH = original_dir


def centre_output(log_exposure_rgb: np.ndarray, stage: str) -> np.ndarray:
    field = np.broadcast_to(
        np.asarray(log_exposure_rgb, dtype=np.float32)[None, None, :],
        (17, 17, 3),
    ).copy()
    if stage == "hd_after_direct_record_mix":
        output = emulsion.record_densities_from_log_exposure(field)
    else:
        density = emulsion.develop_5279_record_density_from_log_exposure(field)
        if stage == "developed_status_m_record_density":
            output = density
        elif stage == "analytical_cmy_amount":
            centre = density[8:9, 8:9]
            return np.asarray(
                emulsion.solve_5279_analytical_cmy_from_status_m_net_density(
                    np.maximum(centre - emulsion.SENSITO_DMIN_RGB, 0.0)
                )[0, 0],
                dtype=np.float64,
            )
        elif stage == "negative_printer_density":
            return np.asarray(
                emulsion.negative_total_printer_density_from_record_density(
                    density[8:9, 8:9]
                )[0, 0],
                dtype=np.float64,
            )
        else:
            raise ValueError(f"unknown stage: {stage}")
    return np.asarray(output[8, 8], dtype=np.float64)


def finite_difference_jacobian(
    log_exposure: float,
    stage: str,
    step: float,
) -> np.ndarray:
    jacobian = np.zeros((3, 3), dtype=np.float64)
    neutral = np.full(3, log_exposure, dtype=np.float64)
    for source in range(3):
        positive = neutral.copy()
        negative = neutral.copy()
        positive[source] += step
        negative[source] -= step
        jacobian[:, source] = (
            centre_output(positive, stage) - centre_output(negative, stage)
        ) / (2.0 * step)
    return jacobian


def summarize_jacobian(jacobian: np.ndarray) -> dict[str, object]:
    source = np.asarray(jacobian, dtype=np.float64)
    absolute = np.abs(source)
    row_total = np.sum(absolute, axis=1)
    diagonal = np.abs(np.diag(source))
    neutral_gamma = np.sum(source, axis=1)
    return {
        "matrix_destination_by_source": source.tolist(),
        "diagonal": np.diag(source).tolist(),
        "signed_neutral_gamma_row_sum": neutral_gamma.tolist(),
        "absolute_off_diagonal_fraction_by_destination": (
            (row_total - diagonal) / np.maximum(row_total, 1.0e-30)
        ).tolist(),
        "separation_to_neutral_gamma_ratio": (
            np.diag(source) / np.maximum(neutral_gamma, 1.0e-30)
        ).tolist(),
        "maximum_absolute_off_diagonal": float(
            np.max(np.abs(source - np.diag(np.diag(source))))
        ),
    }


def measure(*, log_exposures: tuple[float, ...], step: float) -> dict[str, object]:
    v66_profile.apply(emulsion)
    stages = (
        "hd_after_direct_record_mix",
        "developed_status_m_record_density",
        "analytical_cmy_amount",
        "negative_printer_density",
    )
    conditions = {
        "current_record_mix_and_dir": (True, True),
        "record_mix_only_no_interimage_dir": (True, False),
        "interimage_dir_only_identity_record_mix": (False, True),
        "identity_record_mix_no_interimage_dir": (False, False),
    }
    rows: dict[str, list[dict[str, object]]] = {}
    for name, (use_mix, use_dir) in conditions.items():
        condition_rows = []
        with deterministic_coupling(
            record_mix=use_mix, interimage_dir=use_dir
        ):
            for log_exposure in log_exposures:
                condition_rows.append(
                    {
                        "log_exposure": log_exposure,
                        "stages": {
                            stage: summarize_jacobian(
                                finite_difference_jacobian(
                                    log_exposure, stage, step
                                )
                            )
                            for stage in stages
                        },
                    }
                )
        rows[name] = condition_rows

    # The neutral H-D trajectory must not change under either ablation.  Compare
    # the developed Status-M row sums, which are the derivative when all three
    # record exposures move together.
    reference = rows["current_record_mix_and_dir"]
    maximum_neutral_gamma_delta = 0.0
    for condition_rows in rows.values():
        for reference_row, row in zip(reference, condition_rows, strict=True):
            reference_gamma = np.asarray(
                reference_row["stages"]["developed_status_m_record_density"][
                    "signed_neutral_gamma_row_sum"
                ]
            )
            gamma = np.asarray(
                row["stages"]["developed_status_m_record_density"][
                    "signed_neutral_gamma_row_sum"
                ]
            )
            maximum_neutral_gamma_delta = max(
                maximum_neutral_gamma_delta,
                float(np.max(np.abs(gamma - reference_gamma))),
            )

    return {
        "audit": "V71 5279 deterministic record-coupling ownership",
        "profile": v66_profile.PROFILE["name"],
        "image_change": "none",
        "fixture": {
            "uniform_field_shape": [17, 17],
            "log_exposures": list(log_exposures),
            "central_difference_step_loge": step,
            "input_coordinate": "three physical 5279 record log exposures",
            "jacobian_orientation": "destination rows by source columns",
        },
        "upstream_sensitivity_matrix_frozen": (
            emulsion.FILM_RECORD_SENSITIVITY_RGB.tolist()
        ),
        "current_population_record_mix": (
            emulsion.SUBEMULSION_DYE_RECORD_MIX.tolist()
        ),
        "conditions": rows,
        "gates": {
            "maximum_neutral_hd_gamma_delta_across_ablations": {
                "value": maximum_neutral_gamma_delta,
                "limit": 3.0e-4,
                "pass": maximum_neutral_gamma_delta <= 3.0e-4,
            }
        },
        "evidence_boundary": {
            "measured": (
                "neutral H-D and net dye spectra; not colour-separation "
                "Jacobians for 5279"
            ),
            "mechanistically_supported": (
                "record-specific dye formation, masking-coupler spectral "
                "correction and DIR-mediated interimage inhibition"
            ),
            "unidentified": (
                "the direct speed-population source-to-destination record-mix "
                "matrix and the exact 5279 DIR receiver/causer coefficients"
            ),
            "decision_rule": (
                "Identity is the conservative endpoint for an operator with "
                "no independently identified physical observable, but an "
                "image profile requires native-scene and separation-gate review."
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-exposures",
        type=float,
        nargs="+",
        default=list(DEFAULT_LOG_EXPOSURES),
    )
    parser.add_argument("--step", type=float, default=1.0e-3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = measure(log_exposures=tuple(args.log_exposures), step=args.step)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if not all(bool(gate["pass"]) for gate in result["gates"].values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
