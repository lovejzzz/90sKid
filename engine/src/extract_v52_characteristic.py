#!/usr/bin/env python3
"""Reproduce V52's 5279 H-D table from Kodak's March 2003 vector PDF.

This is a research utility, not a runtime dependency.  The PDF itself is not
redistributed.  Its SHA-256 is locked below, and the generated CSV records the
evidence class of every row so graph measurements cannot be confused with the
two explicit endpoint policies.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import sys

import numpy as np


SOURCE_SHA256 = "f76fa5e6b48bbcf6a4a62fe043221af864feb3b517b42d84ebafc431942250c8"

# Page-three graph calibration. X is fixed by the -4/-3/-2/-1/0 ticks. Y is a
# least-squares fit to the D=0 and D=3 border centres plus the printed D=1 and
# D=2 ticks; its density residual RMS is 0.0019466 D.
X0, X1 = 369.236, 553.728
Y_TICKS = np.array([266.723, 205.444, 143.985, 82.230], dtype=np.float64)
D_TICKS = np.array([0.0, 1.0, 2.0, 3.0], dtype=np.float64)

# PDF object identities are locked by SOURCE_SHA256. Curve labels split the
# strokes into several curve/line objects; these groups reconstruct each path.
PATH_GROUPS = {
    "blue": (range(0, 15), (11, 12, 13, 14)),
    "green": (range(15, 25), tuple(range(15, 24))),
    "red": (range(25, 40), tuple(range(24, 28))),
}
SAMPLE_LOGE = np.arange(-3.75, 0.001, 0.25, dtype=np.float64)
ARCHIVE_SHOULDER_INCREMENTS_RGB = np.array(
    [[0.14, 0.22], [0.16, 0.25], [0.12, 0.18]], dtype=np.float64
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(pdf_path: Path) -> list[tuple[float, float, float, float, str]]:
    try:
        import pdfplumber
    except ImportError as error:  # pragma: no cover - research environment guard
        raise RuntimeError("install pdfplumber to reproduce the trace") from error

    actual_sha = _sha256(pdf_path)
    if actual_sha != SOURCE_SHA256:
        raise ValueError(
            f"unexpected 5279 PDF: expected {SOURCE_SHA256}, got {actual_sha}"
        )

    y_slope, y_offset = np.linalg.lstsq(
        np.column_stack((Y_TICKS, np.ones_like(Y_TICKS))),
        D_TICKS,
        rcond=None,
    )[0]
    with pdfplumber.open(pdf_path) as document:
        page = document.pages[2]
        traced: dict[str, np.ndarray] = {}
        path_start_loge: float | None = None
        for name, (curve_indices, line_indices) in PATH_GROUPS.items():
            points: list[tuple[float, float]] = []
            for index in curve_indices:
                points.extend(page.curves[index]["pts"])
            for index in line_indices:
                points.extend(page.lines[index]["pts"])
            xy = np.asarray(points, dtype=np.float64)
            x_values = np.unique(xy[:, 0])
            y_values = np.array(
                [np.mean(xy[xy[:, 0] == x, 1]) for x in x_values],
                dtype=np.float64,
            )
            current_start = -4.0 + 4.0 * (x_values[0] - X0) / (X1 - X0)
            if path_start_loge is None:
                path_start_loge = current_start
            elif not np.isclose(current_start, path_start_loge, atol=1e-9):
                raise ValueError("5279 H-D paths do not share one start coordinate")
            sample_x = X0 + (SAMPLE_LOGE + 4.0) * (X1 - X0) / 4.0
            sample_y = np.interp(sample_x, x_values, y_values)
            start_density = y_slope * y_values[0] + y_offset
            traced[name] = np.concatenate(
                ([start_density, start_density], y_slope * sample_y + y_offset)
            )

    if path_start_loge is None:
        raise RuntimeError("no characteristic paths recovered")
    loge = np.concatenate(([-4.0, path_start_loge], SAMPLE_LOGE))
    rgb = np.column_stack((traced["red"], traced["green"], traced["blue"]))
    rows: list[tuple[float, float, float, float, str]] = []
    for index, exposure in enumerate(loge):
        evidence = (
            "inferred_dmin_hold_before_drawn_path"
            if index == 0
            else "vector_path_start"
            if index == 1
            else "vector_path_interpolation"
        )
        rows.append((exposure, *rgb[index], evidence))
    endpoint = rgb[-1]
    for exposure, increment in zip(
        (0.5, 1.0), ARCHIVE_SHOULDER_INCREMENTS_RGB.T, strict=True
    ):
        density = endpoint + increment
        rows.append(
            (exposure, *density, "inferred_archive_shoulder_increment")
        )
    return rows


def write_csv(rows, destination) -> None:
    writer = csv.writer(destination, lineterminator="\n")
    writer.writerow(
        (
            "log_exposure",
            "red_status_m_density",
            "green_status_m_density",
            "blue_status_m_density",
            "evidence_class",
        )
    )
    for exposure, red, green, blue, evidence in rows:
        writer.writerow(
            (
                f"{exposure:.6f}",
                f"{red:.7f}",
                f"{green:.7f}",
                f"{blue:.7f}",
                evidence,
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = extract(args.pdf)
    if args.output is None:
        write_csv(rows, sys.stdout)
    else:
        with args.output.open("w", encoding="utf-8", newline="") as destination:
            write_csv(rows, destination)


if __name__ == "__main__":
    main()
