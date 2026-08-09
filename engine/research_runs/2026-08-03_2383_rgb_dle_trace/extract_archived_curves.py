"""Extract the vector 2383 sensitometric paths from Kodak H-1-2383t page 5.

Run with the bundled document Python, which provides pdfplumber.  The graph is
vector artwork, so the path coordinates are used directly rather than reading
the rendered PNG.  Each channel is aligned at Kodak's 1.09/1.06/1.03 LAD point
and evaluated at a common relative log exposure whose mean density matches the
seven patent DLE samples.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pdfplumber


OUTPUT = Path(__file__).resolve().parent
PDF = OUTPUT / "kodak_2383_H-1-2383t_2005.pdf"
EXPECTED_SHA256 = "76b692f08eac97fa46ae89d7229fe5f854a958827f4faba78405af204dfe0156"
PATENT_RGB = np.array(
    [
        [4.07832, 4.01495, 4.07676],
        [3.94739, 3.82876, 3.91979],
        [3.72602, 3.50800, 3.73121],
        [3.30847, 3.01825, 3.31323],
        [2.68855, 2.42055, 2.70332],
        [1.89576, 1.72427, 1.96898],
        [1.18055, 1.13752, 1.21653],
    ],
    dtype=np.float64,
)
PATCH_STEPS = np.arange(2, 9)
LAD = {"R": 1.09, "G": 1.06, "B": 1.03}


def extract_curve(page: object, indices: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    graph_left, graph_right = 96.401, 280.833
    graph_top, graph_bottom = 82.489, 267.060
    points = []
    for index in indices:
        for command in page.curves[index]["path"]:
            if command[0] in ("m", "l"):
                points.append(command[1])
    points_array = np.asarray(points, dtype=np.float64)
    log_exposure = -3.0 + (points_array[:, 0] - graph_left) / (
        graph_right - graph_left
    ) * 6.0
    density = (graph_bottom - points_array[:, 1]) / (
        graph_bottom - graph_top
    ) * 6.0
    order = np.argsort(log_exposure)
    log_exposure = log_exposure[order]
    density = density[order]
    unique_log_exposure = np.unique(log_exposure)
    unique_density = np.array(
        [np.mean(density[log_exposure == value]) for value in unique_log_exposure]
    )
    return unique_log_exposure, unique_density


def main() -> None:
    digest = hashlib.sha256(PDF.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"archived sheet hash mismatch: {digest}")
    with pdfplumber.open(PDF) as document:
        page = document.pages[4]
        # PDF vector path order established by graph position and visible B/G/R labels.
        curves = {
            "R": extract_curve(page, (1,)),
            "G": extract_curve(page, (2, 3)),
            "B": extract_curve(page, (4,)),
        }

    lad_log_exposure = {}
    for channel, (log_exposure, density) in curves.items():
        order = np.argsort(density)
        lad_log_exposure[channel] = float(
            np.interp(LAD[channel], density[order], log_exposure[order])
        )

    relative_axis = np.linspace(-2.0, 2.0, 4001)
    model_density = np.stack(
        [
            np.interp(
                relative_axis + lad_log_exposure[channel],
                curves[channel][0],
                curves[channel][1],
            )
            for channel in "RGB"
        ],
        axis=1,
    )
    model_mean = np.mean(model_density, axis=1)
    patent_mean = np.mean(PATENT_RGB, axis=1)
    matched_relative_log_exposure = np.interp(
        patent_mean, model_mean, relative_axis
    )
    predicted = np.stack(
        [
            np.interp(patent_mean, model_mean, model_density[:, channel])
            for channel in range(3)
        ],
        axis=1,
    )
    error = predicted - PATENT_RGB
    patent_red_minus_blue = PATENT_RGB[:, 0] - PATENT_RGB[:, 2]
    predicted_red_minus_blue = predicted[:, 0] - predicted[:, 2]

    with (OUTPUT / "archived_2005_2383_curves.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["channel", "log_exposure_lux_seconds", "status_a_density"])
        for channel in "RGB":
            for log_exposure, density in zip(*curves[channel]):
                writer.writerow([channel, log_exposure, density])

    result = {
        "source": {
            "file": str(PDF),
            "sha256": digest,
            "page": 5,
            "figure_id": "F002_1254AC",
            "revision": "March 2005",
            "pdf_creation_date": "1997-12-05",
            "exposure": "1/500 second tungsten plus Heat Absorbing Glass No. 2043 and Series 1700 filter",
            "process": "ECP-2D",
            "densitometry": "Status A",
        },
        "method": "Direct vector path extraction; each channel horizontally aligned at Kodak LAD R/G/B 1.09/1.06/1.03, then sampled at a common relative log exposure matching each patent step's mean density.",
        "lad_log_exposure_lux_seconds": lad_log_exposure,
        "patch_steps": PATCH_STEPS.astype(int).tolist(),
        "matched_relative_log_exposure": matched_relative_log_exposure.astype(float).tolist(),
        "patent_status_a_rgb": PATENT_RGB.astype(float).tolist(),
        "archived_curve_predicted_status_a_rgb": predicted.astype(float).tolist(),
        "error_rgb_density": error.astype(float).tolist(),
        "all_channel_rmse_density": float(np.sqrt(np.mean(np.square(error)))),
        "channel_rmse_density": np.sqrt(np.mean(np.square(error), axis=0)).astype(float).tolist(),
        "maximum_abs_error_density": float(np.max(np.abs(error))),
        "patent_red_minus_blue_density": patent_red_minus_blue.astype(float).tolist(),
        "archived_curve_predicted_red_minus_blue_density": predicted_red_minus_blue.astype(float).tolist(),
        "red_minus_blue_rmse_density": float(
            np.sqrt(np.mean(np.square(predicted_red_minus_blue - patent_red_minus_blue)))
        ),
        "interpretation_boundary": "The archived sheet plots separated monochromatic sensitometric exposures, while the patent plots a simultaneous control-neutral exposure series. Their disagreement cannot identify a production neutral shaper without measured neutral RGB exposure and cross-talk data.",
    }
    (OUTPUT / "archived_curve_comparison.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
