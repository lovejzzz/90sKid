#!/usr/bin/env python3
"""Extract 2383 sensitivity and dye vectors from Kodak H-1-2383t (2005).

The source PDF is SHA-locked and is not redistributed.  Two tables are
generated at the engine's 20 nm integration wavelengths.  Every value outside
the plotted vector paths has a named extrapolation policy rather than being
silently presented as a measurement.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

import numpy as np


SOURCE_SHA256 = "76b692f08eac97fa46ae89d7229fe5f854a958827f4faba78405af204dfe0156"
SOURCE_MIRROR_SHA256 = (
    "d0f20d7c1a697ed6f1a2a81839e094f7500198c8809e80e93c733f01f1583020"
)
SAMPLE_WAVELENGTHS_NM = np.arange(380.0, 781.0, 20.0, dtype=np.float64)

SENS_X0, SENS_X1 = 74.762, 275.209
SENS_Y_TICKS = np.array(
    [67.486, 105.528, 143.354, 181.288, 219.001], dtype=np.float64
)
SENS_LOG_TICKS = np.array([1.0, 0.0, -1.0, -2.0, -3.0], dtype=np.float64)
# Disconnected graph portions belonging to one emulsion record.  Adjacent PDF
# objects within one tuple are a single continuous stroke split by artwork.
SENSITIVITY_COMPONENTS = {
    "cyan": ((0,), (1,)),
    "magenta": ((2, 3), (4,)),
    "yellow": ((5, 6),),
}
SENSITIVITY_OUTSIDE_PATH_FLOOR = -6.0
SENSITIVITY_PATH_X_TOLERANCE = 0.06  # PDF coordinate rounding, about 0.15 nm

DYE_X0, DYE_X1 = 357.697, 541.928
DYE_Y_TICKS = np.array(
    [246.073, 219.851, 193.497, 167.142, 140.914, 114.560, 88.203, 61.712],
    dtype=np.float64,
)
DYE_DENSITY_TICKS = np.arange(0.0, 1.401, 0.2, dtype=np.float64)
DYE_PATHS = {"cyan": (10,), "magenta": (11, 12), "yellow": (13,)}
VISUAL_NEUTRAL_PATHS = (14, 15)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_points(page, indices: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    points: list[tuple[float, float]] = []
    for index in indices:
        for command in page.curves[index]["path"]:
            if command[0] in ("m", "l"):
                points.append(command[1])
    xy = np.asarray(points, dtype=np.float64)
    order = np.argsort(xy[:, 0], kind="stable")
    xy = xy[order]
    x_values = np.unique(xy[:, 0])
    y_values = np.array(
        [np.mean(xy[xy[:, 0] == x, 1]) for x in x_values], dtype=np.float64
    )
    return x_values, y_values


def _x_for_wavelength(wavelength, x0, x1):
    return x0 + (np.asarray(wavelength) - 250.0) * (x1 - x0) / 500.0


def extract(pdf_path: Path):
    try:
        import pdfplumber
    except ImportError as error:  # pragma: no cover
        raise RuntimeError("install pdfplumber to reproduce the trace") from error
    actual_sha = _sha256(pdf_path)
    if actual_sha not in {SOURCE_SHA256, SOURCE_MIRROR_SHA256}:
        raise ValueError(
            "unexpected 2383 PDF: expected the SHA-locked Kodak source or "
            f"byte-distinct page-identical mirror, got {actual_sha}"
        )

    sensitivity_y_slope, sensitivity_y_offset = np.linalg.lstsq(
        np.column_stack((SENS_Y_TICKS, np.ones_like(SENS_Y_TICKS))),
        SENS_LOG_TICKS,
        rcond=None,
    )[0]
    dye_y_slope, dye_y_offset = np.linalg.lstsq(
        np.column_stack((DYE_Y_TICKS, np.ones_like(DYE_Y_TICKS))),
        DYE_DENSITY_TICKS,
        rcond=None,
    )[0]

    with pdfplumber.open(pdf_path) as document:
        page = document.pages[5]
        sample_sens_x = _x_for_wavelength(
            SAMPLE_WAVELENGTHS_NM, SENS_X0, SENS_X1
        )
        sensitivity: dict[str, np.ndarray] = {}
        sensitivity_evidence: dict[str, list[str]] = {}
        for name, component_groups in SENSITIVITY_COMPONENTS.items():
            components = []
            active = np.zeros(SAMPLE_WAVELENGTHS_NM.size, dtype=bool)
            for indices in component_groups:
                x_values, y_values = _path_points(page, indices)
                log_values = sensitivity_y_slope * y_values + sensitivity_y_offset
                within = (
                    sample_sens_x >= x_values[0] - SENSITIVITY_PATH_X_TOLERANCE
                ) & (
                    sample_sens_x <= x_values[-1] + SENSITIVITY_PATH_X_TOLERANCE
                )
                component = np.full(
                    SAMPLE_WAVELENGTHS_NM.size,
                    SENSITIVITY_OUTSIDE_PATH_FLOOR,
                    dtype=np.float64,
                )
                component[within] = np.interp(
                    sample_sens_x[within], x_values, log_values
                )
                components.append(component)
                active |= within
            # The components are disconnected portions of one plotted record,
            # not independent emulsions whose sensitivities should be summed.
            sensitivity[name] = np.max(np.stack(components), axis=0)
            sensitivity_evidence[name] = [
                "vector_path_interpolation"
                if is_active
                else "explicit_below_graph_floor_log10_-6"
                for is_active in active
            ]

        sample_dye_x = _x_for_wavelength(
            SAMPLE_WAVELENGTHS_NM, DYE_X0, DYE_X1
        )
        dye: dict[str, np.ndarray] = {}
        dye_evidence: dict[str, list[str]] = {}
        for name, indices in DYE_PATHS.items():
            x_values, y_values = _path_points(page, indices)
            density_values = dye_y_slope * y_values + dye_y_offset
            values = np.interp(
                sample_dye_x,
                x_values,
                density_values,
                left=density_values[0],
                right=density_values[-1],
            )
            evidence = []
            for index, sample_x in enumerate(sample_dye_x):
                if sample_x < x_values[0]:
                    evidence.append("explicit_constant_hold_before_drawn_path")
                elif sample_x <= x_values[-1]:
                    evidence.append("vector_path_interpolation")
                else:
                    # Continue the last measured secant only until zero.  This
                    # affects 760/780 nm beyond the graph's 750 nm boundary.
                    dx = x_values[-1] - x_values[-2]
                    slope = (density_values[-1] - density_values[-2]) / dx
                    values[index] = max(
                        density_values[-1] + slope * (sample_x - x_values[-1]),
                        0.0,
                    )
                    evidence.append("inferred_terminal_secant_clipped_at_zero")
            dye[name] = values
            dye_evidence[name] = evidence

        neutral_x, neutral_y = _path_points(page, VISUAL_NEUTRAL_PATHS)
        neutral_density = dye_y_slope * neutral_y + dye_y_offset
        visual_neutral = np.interp(
            sample_dye_x,
            neutral_x,
            neutral_density,
            left=neutral_density[0],
            right=neutral_density[-1],
        )
        visual_neutral_evidence: list[str] = []
        for index, sample_x in enumerate(sample_dye_x):
            if sample_x < neutral_x[0]:
                visual_neutral_evidence.append(
                    "explicit_constant_hold_before_drawn_path"
                )
            elif sample_x <= neutral_x[-1]:
                visual_neutral_evidence.append("vector_path_interpolation")
            else:
                dx = neutral_x[-1] - neutral_x[-2]
                slope = (neutral_density[-1] - neutral_density[-2]) / dx
                visual_neutral[index] = max(
                    neutral_density[-1]
                    + slope * (sample_x - neutral_x[-1]),
                    0.0,
                )
                visual_neutral_evidence.append(
                    "inferred_terminal_secant_clipped_at_zero"
                )

    return (
        sensitivity,
        sensitivity_evidence,
        dye,
        dye_evidence,
        visual_neutral,
        visual_neutral_evidence,
    )


def _write_sensitivity(path, values, evidence) -> None:
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(
            [
                "wavelength_nm",
                "cyan_log_sensitivity",
                "magenta_log_sensitivity",
                "yellow_log_sensitivity",
                "cyan_evidence_class",
                "magenta_evidence_class",
                "yellow_evidence_class",
            ]
        )
        for index, wavelength in enumerate(SAMPLE_WAVELENGTHS_NM):
            writer.writerow(
                [
                    f"{wavelength:.1f}",
                    *(f"{values[name][index]:.9f}" for name in ("cyan", "magenta", "yellow")),
                    *(evidence[name][index] for name in ("cyan", "magenta", "yellow")),
                ]
            )


def _write_dye(path, values, evidence) -> None:
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(
            [
                "wavelength_nm",
                "cyan_relative_density",
                "magenta_relative_density",
                "yellow_relative_density",
                "cyan_evidence_class",
                "magenta_evidence_class",
                "yellow_evidence_class",
            ]
        )
        for index, wavelength in enumerate(SAMPLE_WAVELENGTHS_NM):
            writer.writerow(
                [
                    f"{wavelength:.1f}",
                    *(f"{values[name][index]:.9f}" for name in ("cyan", "magenta", "yellow")),
                    *(evidence[name][index] for name in ("cyan", "magenta", "yellow")),
                ]
            )


def _write_visual_neutral(path, values, evidence) -> None:
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(
            ["wavelength_nm", "visual_neutral_density", "evidence_class"]
        )
        for index, wavelength in enumerate(SAMPLE_WAVELENGTHS_NM):
            writer.writerow(
                [f"{wavelength:.1f}", f"{values[index]:.9f}", evidence[index]]
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    sensitivity, sensitivity_e, dye, dye_e, neutral, neutral_e = extract(
        args.pdf
    )
    _write_sensitivity(
        args.output_directory / "2383_log_sensitivity_trace_2005.csv",
        sensitivity,
        sensitivity_e,
    )
    _write_dye(
        args.output_directory / "2383_dye_density_trace_2005.csv", dye, dye_e
    )
    _write_visual_neutral(
        args.output_directory / "2383_visual_neutral_trace_2005.csv",
        neutral,
        neutral_e,
    )


if __name__ == "__main__":
    main()
