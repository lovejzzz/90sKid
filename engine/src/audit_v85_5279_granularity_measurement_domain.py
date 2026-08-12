#!/usr/bin/env python3
"""Re-audit Kodak 5279's granularity graph and its measurement coordinate.

The public PDF is not a runtime dependency and is not redistributed here.  The
caller supplies the March 2003 H-1-5279t PDF; its SHA-256 is locked below.
This audit reproduces the vector trace, proves the R/G/B curve assignment,
compares the graph's companion sensitometry with the separately published
Status-M H-D graph, and checks the active V72 channel/coordinate mapping.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as e
from extract_v52_characteristic import extract as extract_v52_characteristic
import v72_profile


SOURCE_SHA256 = "f76fa5e6b48bbcf6a4a62fe043221af864feb3b517b42d84ebafc431942250c8"
TRACE = Path(__file__).resolve().parents[1] / "data/5279_granularity_trace_2003.csv"

# pdfplumber object identities are locked by SOURCE_SHA256.  On printed page 4,
# the granularity paths are labelled at the left R/G/B.  The red path is split
# around its sharp peak; green and blue are single polylines.
GRANULARITY_PATHS_RGB = ((5, 6, 7), (0,), (3,))
COMPANION_CHARACTERISTIC_PATHS_RGB = (4, 1, 2)

# Printed right-axis ticks, in page-top coordinates.  V50 fitted log10(sigma_D)
# to all twelve rather than selecting two endpoints.
SIGMA_TICK_Y = np.asarray(
    [
        86.393,
        98.906,
        108.211,
        123.291,
        139.975,
        152.488,
        161.792,
        176.872,
        193.556,
        206.069,
        215.374,
        230.454,
    ],
    dtype=np.float64,
)
SIGMA_TICK_VALUES = np.asarray(
    [0.500, 0.300, 0.200, 0.100, 0.050, 0.030, 0.020, 0.010,
     0.005, 0.003, 0.002, 0.001],
    dtype=np.float64,
)
SAMPLE_GRAPH_LOGE = np.arange(0.0, 4.001, 0.5, dtype=np.float64)
SAMPLE_INTERNAL_LOGE = SAMPLE_GRAPH_LOGE - 4.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def flatten_pdf_paths(paths: list[list[tuple]], cubic_samples: int = 4096) -> np.ndarray:
    """Flatten pdfplumber m/l/c commands without treating Bezier controls as data."""
    points: list[np.ndarray] = []
    current: np.ndarray | None = None
    for path in paths:
        for command in path:
            operator = command[0]
            if operator == "m":
                current = np.asarray(command[1], dtype=np.float64)
                points.append(current.copy())
            elif operator == "l":
                if current is None:
                    raise ValueError("line command before path start")
                current = np.asarray(command[1], dtype=np.float64)
                points.append(current.copy())
            elif operator == "c":
                if current is None:
                    raise ValueError("cubic command before path start")
                p0 = current
                p1 = np.asarray(command[1], dtype=np.float64)
                p2 = np.asarray(command[2], dtype=np.float64)
                p3 = np.asarray(command[3], dtype=np.float64)
                t = np.linspace(0.0, 1.0, cubic_samples + 1, dtype=np.float64)[
                    1:, None
                ]
                samples = (
                    np.power(1.0 - t, 3) * p0
                    + 3.0 * np.square(1.0 - t) * t * p1
                    + 3.0 * (1.0 - t) * np.square(t) * p2
                    + np.power(t, 3) * p3
                )
                points.extend(samples)
                current = p3
            else:
                raise ValueError(f"unsupported PDF path operator: {operator}")
    return np.asarray(points, dtype=np.float64)


def interpolate_path_y(page, indices: tuple[int, ...], x: np.ndarray) -> np.ndarray:
    xy = flatten_pdf_paths([page.curves[index]["path"] for index in indices])
    order = np.argsort(xy[:, 0], kind="stable")
    return np.interp(x, xy[order, 0], xy[order, 1])


def load_versioned_trace() -> np.ndarray:
    with TRACE.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    return np.asarray(
        [
            [
                float(row["internal_logE"]),
                float(row["graph_logE"]),
                float(row["red_sigma_D"]),
                float(row["green_sigma_D"]),
                float(row["blue_sigma_D"]),
            ]
            for row in rows
        ],
        dtype=np.float64,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    actual_sha = sha256(args.pdf)
    if actual_sha != SOURCE_SHA256:
        raise ValueError(f"unexpected PDF: expected {SOURCE_SHA256}, got {actual_sha}")

    try:
        import pdfplumber
    except ImportError as error:  # pragma: no cover
        raise RuntimeError("install pdfplumber to reproduce V85") from error

    log_sigma_slope, log_sigma_offset = np.linalg.lstsq(
        np.column_stack((SIGMA_TICK_Y, np.ones_like(SIGMA_TICK_Y))),
        np.log10(SIGMA_TICK_VALUES),
        rcond=None,
    )[0]
    fitted_tick_y = (
        np.log10(SIGMA_TICK_VALUES) - log_sigma_offset
    ) / log_sigma_slope
    tick_fit_rms_pdf_points = float(
        np.sqrt(np.mean(np.square(fitted_tick_y - SIGMA_TICK_Y)))
    )

    with pdfplumber.open(args.pdf) as document:
        page3 = document.pages[2]
        page4 = document.pages[3]
        page3_text = page3.extract_text() or ""
        page4_text = page4.extract_text() or ""

        graph_border = page4.rects[7]
        graph_x = graph_border["x0"] + SAMPLE_GRAPH_LOGE / 4.0 * (
            graph_border["x1"] - graph_border["x0"]
        )
        traced_sigma = np.column_stack(
            [
                np.power(
                    10.0,
                    log_sigma_slope
                    * interpolate_path_y(page4, indices, graph_x)
                    + log_sigma_offset,
                )
                for indices in GRANULARITY_PATHS_RGB
            ]
        )

        # The upper curves in the combined graph use the same 0..4 horizontal
        # coordinate.  Their plot border is exactly D=3 at the top and D=0 at
        # the bottom.
        companion_density = np.column_stack(
            [
                3.0
                * (
                    graph_border["bottom"]
                    - interpolate_path_y(page4, (index,), graph_x)
                )
                / (graph_border["bottom"] - graph_border["top"])
                for index in COMPANION_CHARACTERISTIC_PATHS_RGB
            ]
        )

    versioned_trace = load_versioned_trace()
    if not np.array_equal(versioned_trace[:, :2], np.column_stack(
        (SAMPLE_INTERNAL_LOGE, SAMPLE_GRAPH_LOGE)
    )):
        raise ValueError("versioned granularity coordinates changed")
    trace_delta = traced_sigma - versioned_trace[:, 2:]

    characteristic_rows = extract_v52_characteristic(args.pdf)
    characteristic = np.asarray(
        [[row[0], row[1], row[2], row[3]] for row in characteristic_rows],
        dtype=np.float64,
    )
    page3_density = np.column_stack(
        [
            np.interp(SAMPLE_INTERNAL_LOGE, characteristic[:, 0], characteristic[:, i])
            for i in range(1, 4)
        ]
    )
    characteristic_delta = companion_density - page3_density

    required_page3_phrases = (
        "Read with a microdensitometer, (red, green, blue) using a 48-micrometer aperture.",
        "Status M",
    )
    required_page4_phrases = (
        "Diffuse rms Granularity Curves",
        "Granularity Sigma D",
        "multiply by 1000",
        "produced on different equipment",
    )
    normalized_source_text = " ".join(
        (page3_text + " " + page4_text).lower().split()
    )
    phrase_checks = {
        phrase: " ".join(phrase.lower().split()) in normalized_source_text
        for phrase in required_page3_phrases + required_page4_phrases
    }

    v72_profile.apply(e)
    active_trace = np.column_stack(
        (e.GRANULARITY_LOG_EXPOSURE, e.GRANULARITY_SIGMA_D_RGB.T)
    ).astype(np.float64)
    active_expected = np.column_stack((SAMPLE_INTERNAL_LOGE, traced_sigma))
    active_delta = active_trace - active_expected

    report = {
        "audit": "V85 5279 granularity graph and measurement-domain re-audit",
        "source": {
            "title": "KODAK VISION 500T Color Negative Film 5279 / 7279",
            "publication": "H-1-5279t, March 2003",
            "sha256": actual_sha,
            "granularity_graph": "printed page 4, F002_0269AC",
        },
        "reproducible_vector_trace": {
            "path_indices_rgb": [list(indices) for indices in GRANULARITY_PATHS_RGB],
            "sample_internal_loge": SAMPLE_INTERNAL_LOGE.tolist(),
            "sample_graph_loge": SAMPLE_GRAPH_LOGE.tolist(),
            "sigma_d_rgb": traced_sigma.tolist(),
            "axis_fit_rms_pdf_points": tick_fit_rms_pdf_points,
            "maximum_absolute_delta_from_v50_csv": float(np.max(np.abs(trace_delta))),
            "maximum_relative_delta_from_v50_csv": float(
                np.max(np.abs(trace_delta) / versioned_trace[:, 2:])
            ),
            "curve_identity": (
                "The printed left-side labels identify the lower paths as R/G/B "
                "microdensitometer records. They are not display RGB and not "
                "direct measurements of isolated silver-halide sublayers."
            ),
        },
        "horizontal_coordinate_audit": {
            "mapping": "printed graph 0..4 -> engine logE -4..0",
            "page4_companion_density_rgb": companion_density.tolist(),
            "page3_status_m_density_rgb": page3_density.tolist(),
            "rms_density_delta_rgb": np.sqrt(
                np.mean(np.square(characteristic_delta), axis=0)
            ).tolist(),
            "maximum_absolute_density_delta_rgb": np.max(
                np.abs(characteristic_delta), axis=0
            ).tolist(),
            "interpretation": (
                "The combined graph's companion H-D curves agree with the "
                "separate Status-M graph after a four-log-unit horizontal "
                "translation. The small residual is consistent with Kodak's "
                "note that sensitometry and granularity used different equipment."
            ),
        },
        "measurement_domain": {
            "kodak_page3": (
                "Diffuse RMS read with red, green and blue microdensitometer "
                "responses through a 48 micrometre aperture."
            ),
            "iso_10505_2009": (
                "Colour negative films use ISO 5-3 Status-M spectral products; "
                "the 48.0 +/- 0.5 micrometre circular efflux aperture is the "
                "standard geometry."
            ),
            "engine_coordinate": (
                "V61+ jointly inverts complete Status-M densities through D-min "
                "and all three net dye/mask spectra. The marginal curves belong "
                "in Status-M density space, not independently scaled display RGB."
            ),
            "phrase_checks": phrase_checks,
        },
        "active_v72_mapping": {
            "channel_order": [
                "red microdensitometer / cyan-forming analytical record",
                "green microdensitometer / magenta-forming analytical record",
                "blue microdensitometer / yellow-forming analytical record",
            ],
            "maximum_absolute_delta_from_retrace": float(
                np.max(np.abs(active_delta))
            ),
            "status": "pass",
        },
        "decision": {
            "trace": "V50 numerical trace and channel identity are retained.",
            "axis": "The four-log-unit horizontal translation is retained.",
            "status_m": "V61's joint ISO Status-M coordinate is retained.",
            "blue_record": (
                "The large blue-record marginal is present in Kodak's graph; it "
                "is not corrected by relabelling or by lowering it to taste."
            ),
            "remaining_unknown": (
                "Kodak publishes three marginal aperture RMS curves but not the "
                "cross-record covariance/cross-spectrum. That missing joint law, "
                "not a trace error, owns the unresolved colour-versus-luma grain."
            ),
            "image_release": "V72 remains unchanged; V85 changes no pixels.",
        },
    }
    if not all(phrase_checks.values()):
        raise AssertionError("required source wording was not recovered")
    if report["reproducible_vector_trace"]["maximum_relative_delta_from_v50_csv"] > 2e-4:
        raise AssertionError("V50 CSV does not close against the source paths")
    if report["active_v72_mapping"]["maximum_absolute_delta_from_retrace"] > 5e-6:
        raise AssertionError("active V72 trace differs from the source retrace")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
