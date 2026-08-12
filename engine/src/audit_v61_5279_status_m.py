#!/usr/bin/env python3
"""Audit V61's ISO Status-M and joint 5279 analytical coordinate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v60_profile
import v61_profile


TRACE = Path(__file__).resolve().parents[1] / "data/5279_spectral_trace_2003.csv"
ISHII_5218_PRINTING_DENSITY_MATRIX = np.asarray(
    [
        [4.049, 0.303, 0.072],
        [0.472, 3.090, 0.191],
        [0.248, 0.397, 2.913],
    ],
    dtype=np.float64,
)


def row_normalized(matrix: np.ndarray) -> np.ndarray:
    return matrix / np.diag(matrix)[:, None]


def printer_density_jacobian(point: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    point = np.asarray(point, dtype=np.float32)
    origin = e.apply_5279_to_2383_printer_density_lut(point).astype(np.float64)
    step = 1e-3
    jacobian = np.column_stack(
        [
            (
                e.apply_5279_to_2383_printer_density_lut(
                    point + np.eye(3, dtype=np.float32)[channel] * step
                ).astype(np.float64)
                - origin
            )
            / step
            for channel in range(3)
        ]
    )
    return origin, jacobian


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--record-density-sample",
        type=Path,
        help="optional HxWx3 V60 net Status-M density sample",
    )
    args = parser.parse_args()

    trace = np.genfromtxt(TRACE, delimiter=",", names=True)
    dye = np.column_stack(
        [
            trace["cyan_net_density"],
            trace["magenta_net_density"],
            trace["yellow_net_density"],
        ]
    )
    midscale_net_spectrum = (
        trace["midscale_neutral_density"] - trace["minimum_density"]
    )
    midscale_coefficients = np.linalg.lstsq(
        dye, midscale_net_spectrum, rcond=None
    )[0]
    midscale_reconstruction = (
        trace["minimum_density"] + dye @ midscale_coefficients
    )
    midscale_error = (
        midscale_reconstruction - trace["midscale_neutral_density"]
    )

    v60_profile.apply(e)
    archive_weights = e._negative_5279_status_m_weights().astype(np.float64)
    archive_axis = e.NEGATIVE_5279_STATUS_M_WAVELENGTHS_NM.astype(np.float64)
    archive_output, archive_jacobian = printer_density_jacobian(
        np.asarray([0.7, 0.8, 0.8], dtype=np.float32)
    )

    v61_profile.apply(e)
    iso_weights = e._negative_5279_status_m_weights().astype(np.float64)
    iso_axis = e.NEGATIVE_5279_STATUS_M_WAVELENGTHS_NM.astype(np.float64)
    archive_on_iso = np.column_stack(
        [
            np.interp(iso_axis, archive_axis, archive_weights[:, channel])
            for channel in range(3)
        ]
    )
    archive_on_iso /= np.sum(archive_on_iso, axis=0, keepdims=True)
    cosine = np.sum(archive_on_iso * iso_weights, axis=0) / np.sqrt(
        np.sum(np.square(archive_on_iso), axis=0)
        * np.sum(np.square(iso_weights), axis=0)
    )
    l1 = np.sum(np.abs(archive_on_iso - iso_weights), axis=0)

    trace_dmin = np.interp(
        iso_axis, trace["wavelength_nm"], trace["minimum_density"]
    )
    trace_midscale = np.interp(
        iso_axis, trace["wavelength_nm"], trace["midscale_neutral_density"]
    )
    dmin_status_m = -np.log10(np.power(10.0, -trace_dmin) @ iso_weights)
    midscale_status_m = -np.log10(
        np.power(10.0, -trace_midscale) @ iso_weights
    )
    midscale_status_m_net = midscale_status_m - dmin_status_m
    recovered_midscale = (
        e.solve_5279_analytical_cmy_from_status_m_net_density(
            midscale_status_m_net
        )
    )
    closed_midscale = (
        e.negative_5279_status_m_net_density_from_analytical_cmy(
            recovered_midscale
        )
    )

    axis = np.linspace(0.0, e.NEGATIVE_5279_MAX_RECORD_DENSITY, 29)
    target_cube = np.stack(
        np.meshgrid(axis, axis, axis, indexing="ij"), axis=-1
    )
    analytical_cube = e.build_5279_analytical_cmy_lut(29)
    reconstructed_cube = (
        e.negative_5279_status_m_net_density_from_analytical_cmy(
            analytical_cube
        )
    )
    cube_error = reconstructed_cube - target_cube
    v61_output, v61_jacobian = printer_density_jacobian(
        np.asarray([0.7, 0.8, 0.8], dtype=np.float32)
    )

    actual_sample = None
    if args.record_density_sample is not None:
        sample = np.load(args.record_density_sample).reshape(-1, 3)
        analytical = e.solve_5279_analytical_cmy_from_status_m_net_density(
            sample
        )
        reconstructed = (
            e.negative_5279_status_m_net_density_from_analytical_cmy(
                analytical
            )
        )
        error = reconstructed - sample
        actual_sample = {
            "path": str(args.record_density_sample),
            "samples": int(sample.shape[0]),
            "rms_density_error_rgb": np.sqrt(np.mean(np.square(error), axis=0)).tolist(),
            "maximum_absolute_density_error_rgb": np.max(np.abs(error), axis=0).tolist(),
            "exactly_reachable_fraction_at_1e-5D": float(
                np.mean(np.max(np.abs(error), axis=1) < 1e-5)
            ),
            "any_nonnegative_boundary_fraction": float(
                np.mean(np.any(analytical < 1e-8, axis=1))
            ),
        }

    report = {
        "v61_profile": v61_profile.PROFILE,
        "midscale_neutral_spectral_decomposition": {
            "analytical_cmy_coefficients": midscale_coefficients.tolist(),
            "rms_spectral_density_error": float(
                np.sqrt(np.mean(np.square(midscale_error)))
            ),
            "maximum_absolute_spectral_density_error": float(
                np.max(np.abs(midscale_error))
            ),
            "iso_status_m_total_density_rgb": midscale_status_m.tolist(),
            "iso_status_m_dmin_rgb": dmin_status_m.tolist(),
            "iso_status_m_net_density_rgb": midscale_status_m_net.tolist(),
            "joint_inverse_cmy": recovered_midscale.tolist(),
            "joint_inverse_closure_error_rgb": (
                closed_midscale - midscale_status_m_net
            ).tolist(),
        },
        "status_m_receiver_correction": {
            "archive_peak_wavelengths_rgb": archive_axis[
                np.argmax(archive_weights, axis=0)
            ].tolist(),
            "iso_peak_wavelengths_rgb": iso_axis[
                np.argmax(iso_weights, axis=0)
            ].tolist(),
            "archive_to_iso_cosine_rgb": cosine.tolist(),
            "archive_to_iso_l1_rgb": l1.tolist(),
        },
        "independent_density_cube_physical_gamut": {
            "rms_projection_error_rgb": np.sqrt(
                np.mean(np.square(cube_error), axis=(0, 1, 2))
            ).tolist(),
            "maximum_absolute_projection_error_rgb": np.max(
                np.abs(cube_error), axis=(0, 1, 2)
            ).tolist(),
            "exactly_reachable_fraction_at_1e-5D": float(
                np.mean(np.max(np.abs(cube_error), axis=-1) < 1e-5)
            ),
            "interpretation": (
                "The full independent Status-M cube is not the physical gamut "
                "of a masked three-dye negative; real developed records are "
                "the relevant validation domain."
            ),
        },
        "negative_to_2383_printing_density_local_audit": {
            "point_status_m_net_rgb": [0.7, 0.8, 0.8],
            "v60_output_rgb": archive_output.tolist(),
            "v60_jacobian": archive_jacobian.tolist(),
            "v60_row_normalized_jacobian": row_normalized(
                archive_jacobian
            ).tolist(),
            "v61_output_rgb": v61_output.tolist(),
            "v61_jacobian": v61_jacobian.tolist(),
            "v61_row_normalized_jacobian": row_normalized(v61_jacobian).tolist(),
            "published_ek5218_to_2383_matrix": (
                ISHII_5218_PRINTING_DENSITY_MATRIX.tolist()
            ),
            "published_ek5218_row_normalized": row_normalized(
                ISHII_5218_PRINTING_DENSITY_MATRIX
            ).tolist(),
            "boundary": (
                "EK5218 is a cross-stock witness, not a substitute for an "
                "unpublished EK5279 matrix."
            ),
        },
        "real_material_sample": actual_sample,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    v60_profile.apply(e)


if __name__ == "__main__":
    main()
