#!/usr/bin/env python3
"""Reproduce the V53 2383 Status-A H-D table from Kodak's 2005 vector PDF.

This research utility keeps the source sheet outside the repository.  Its
SHA-256 and vector-object identities are locked here.  Unlike a regular 0.1
log-exposure digitisation, the emitted common axis contains the union of every
original vector node, so interpolating the CSV reproduces every published path
vertex without adding a second resampling error.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import sys

import numpy as np


SOURCE_SHA256 = "76b692f08eac97fa46ae89d7229fe5f854a958827f4faba78405af204dfe0156"

# Page-five graph calibration.  The horizontal border is labelled -3..+3.
# Density is a least-squares fit to the seven printed 0..6 grid lines; its
# residual RMS is 0.0009894 Status-A density.
X0, X1 = 96.401, 280.833
Y_TICKS = np.array(
    [267.060, 236.360, 205.536, 174.836, 144.013, 113.312, 82.489],
    dtype=np.float64,
)
D_TICKS = np.arange(7, dtype=np.float64)

# PDF vector path order established from the printed R/G/B labels and graph
# position.  Green is split into two adjacent path objects by the PDF artwork.
PATH_GROUPS = {"red": (1,), "green": (2, 3), "blue": (4,)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _curve_points(page, indices: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
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


def extract(pdf_path: Path) -> list[tuple[float, float, float, float, str, str, str]]:
    try:
        import pdfplumber
    except ImportError as error:  # pragma: no cover - research environment guard
        raise RuntimeError("install pdfplumber to reproduce the trace") from error

    actual_sha = _sha256(pdf_path)
    if actual_sha != SOURCE_SHA256:
        raise ValueError(
            f"unexpected 2383 PDF: expected {SOURCE_SHA256}, got {actual_sha}"
        )

    y_slope, y_offset = np.linalg.lstsq(
        np.column_stack((Y_TICKS, np.ones_like(Y_TICKS))),
        D_TICKS,
        rcond=None,
    )[0]
    with pdfplumber.open(pdf_path) as document:
        page = document.pages[4]
        vectors = {
            name: _curve_points(page, indices)
            for name, indices in PATH_GROUPS.items()
        }

    # Preserve every original path vertex on one axis, with only two explicit
    # non-vector endpoints to disclose the behaviour outside each drawn path.
    union_x = np.unique(
        np.concatenate(
            ([X0, X1], *(vector[0] for vector in vectors.values()))
        )
    )
    log_exposure = -3.0 + 6.0 * (union_x - X0) / (X1 - X0)

    densities: dict[str, np.ndarray] = {}
    evidence: dict[str, list[str]] = {}
    for name, (x_values, y_values) in vectors.items():
        vector_density = y_slope * y_values + y_offset
        densities[name] = np.interp(
            union_x,
            x_values,
            vector_density,
            left=vector_density[0],
            right=vector_density[-1],
        )
        evidence[name] = [
            "explicit_dmin_hold_before_drawn_path"
            if x < x_values[0]
            else "explicit_dmax_hold_after_drawn_path"
            if x > x_values[-1]
            else "vector_path_node_or_interpolation"
            for x in union_x
        ]

    return [
        (
            exposure,
            densities["red"][index],
            densities["green"][index],
            densities["blue"][index],
            evidence["red"][index],
            evidence["green"][index],
            evidence["blue"][index],
        )
        for index, exposure in enumerate(log_exposure)
    ]


def write_csv(rows, destination) -> None:
    writer = csv.writer(destination, lineterminator="\n")
    writer.writerow(
        (
            "log_exposure",
            "red_status_a_density",
            "green_status_a_density",
            "blue_status_a_density",
            "red_evidence_class",
            "green_evidence_class",
            "blue_evidence_class",
        )
    )
    for exposure, red, green, blue, red_e, green_e, blue_e in rows:
        writer.writerow(
            (
                f"{exposure:.9f}",
                f"{red:.9f}",
                f"{green:.9f}",
                f"{blue:.9f}",
                red_e,
                green_e,
                blue_e,
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
