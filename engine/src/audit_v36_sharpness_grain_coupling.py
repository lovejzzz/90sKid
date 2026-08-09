#!/usr/bin/env python3
"""Audit V36 5279 sharpness and granularity on one physical 35 mm scale.

Kodak's H-1-5279t graph is a processed-stock signal MTF, while its diffuse RMS
curves are density-fluctuation measurements made with a 48 micrometre aperture.
They are related perceptually but are not the same quantity.  This audit keeps
their units explicit and verifies that the fitted MTF lies inside broad ranges
visually digitized from the official graph; the ranges are deliberately not a
new colour or sharpness fit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v36_profile


FILM_IMAGE_WIDTH_MM = 24.9
NATIVE_WIDTH_PX = 5760
CHANNELS = ("R", "G", "B")

# Broad reading intervals from Kodak H-1-5279t page 3.  The source graph is
# small and logarithmic, so these are validation envelopes, not digitized truth.
OFFICIAL_MTF_ENVELOPES_PERCENT = {
    3.0: ((100.0, 115.0), (100.0, 115.0), (100.0, 115.0)),
    10.0: ((90.0, 108.0), (103.0, 120.0), (110.0, 128.0)),
    20.0: ((80.0, 98.0), (98.0, 118.0), (108.0, 132.0)),
    50.0: ((35.0, 58.0), (58.0, 82.0), (62.0, 88.0)),
    75.0: ((18.0, 36.0), (34.0, 56.0), (38.0, 58.0)),
}


def fitted_mtf(frequency_cycles_per_mm: np.ndarray) -> np.ndarray:
    pixels_per_mm = NATIVE_WIDTH_PX / FILM_IMAGE_WIDTH_MM
    frequency_cycles_per_pixel = frequency_cycles_per_mm / pixels_per_mm
    core = e.NEGATIVE_MTF_CORE_SIGMA_RGB.astype(np.float64)
    adjacency = e.NEGATIVE_MTF_ADJACENCY_AMOUNT_RGB.astype(np.float64)
    mid = float(e.NEGATIVE_MTF_ADJACENCY_MID_SIGMA_PX_5760)
    broad = float(e.NEGATIVE_MTF_ADJACENCY_BROAD_SIGMA_PX_5760)

    def gaussian(sigma: np.ndarray | float) -> np.ndarray:
        return np.exp(
            -2.0
            * np.pi**2
            * np.square(frequency_cycles_per_pixel[:, None])
            * np.square(np.asarray(sigma, dtype=np.float64))
        )

    return gaussian(core) + adjacency * (gaussian(mid) - gaussian(broad))


def first_crossing(frequencies: np.ndarray, response: np.ndarray, level: float) -> float:
    peak_index = int(np.argmax(response))
    after_peak = np.flatnonzero(response[peak_index:] <= level)
    if not after_peak.size:
        return float("nan")
    right = peak_index + int(after_peak[0])
    if right == 0:
        return float(frequencies[0])
    left = right - 1
    x0, x1 = frequencies[left], frequencies[right]
    y0, y1 = response[left], response[right]
    return float(x0 + (level - y0) * (x1 - x0) / (y1 - y0))


def edge_widths() -> list[float]:
    image = np.zeros((8, NATIVE_WIDTH_PX, 3), dtype=np.float32)
    image[:, NATIVE_WIDTH_PX // 2 :, :] = 1.0
    response = e.apply_5279_mtf(image, 1.0)[4]
    widths = []
    micrometres_per_pixel = FILM_IMAGE_WIDTH_MM * 1000.0 / NATIVE_WIDTH_PX

    def crossing(line: np.ndarray, level: float) -> float:
        right = int(np.flatnonzero(line >= level)[0])
        left = max(0, right - 1)
        if right == left or line[right] == line[left]:
            return float(right)
        return float(
            left + (level - line[left]) / (line[right] - line[left])
        )

    for channel in range(3):
        line = response[:, channel]
        x10 = crossing(line, 0.1)
        x90 = crossing(line, 0.9)
        widths.append((x90 - x10) * micrometres_per_pixel)
    return widths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    v36_profile.apply(e)

    nyquist = (NATIVE_WIDTH_PX / FILM_IMAGE_WIDTH_MM) / 2.0
    dense_frequencies = np.linspace(0.0, nyquist, 10001)
    dense_response = fitted_mtf(dense_frequencies)
    sample_frequencies = np.array(sorted(OFFICIAL_MTF_ENVELOPES_PERCENT))
    samples = fitted_mtf(sample_frequencies) * 100.0
    sample_rows = []
    every_sample_in_envelope = True
    for frequency, values in zip(sample_frequencies, samples, strict=True):
        envelopes = OFFICIAL_MTF_ENVELOPES_PERCENT[float(frequency)]
        inside = [
            bool(low <= value <= high)
            for value, (low, high) in zip(values, envelopes, strict=True)
        ]
        every_sample_in_envelope &= all(inside)
        sample_rows.append(
            {
                "frequency_cycles_per_mm": float(frequency),
                "fitted_response_percent_rgb": values.tolist(),
                "official_visual_envelope_percent_rgb": [list(x) for x in envelopes],
                "inside_envelope_rgb": inside,
            }
        )

    aperture_pixels = (
        e.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
        * 1e-3
        * NATIVE_WIDTH_PX
        / FILM_IMAGE_WIDTH_MM
    )
    report = {
        "profile": v36_profile.PROFILE["version_id"],
        "physical_scale": {
            "film_image_width_mm": FILM_IMAGE_WIDTH_MM,
            "native_width_pixels": NATIVE_WIDTH_PX,
            "pixel_pitch_micrometres": FILM_IMAGE_WIDTH_MM * 1000.0 / NATIVE_WIDTH_PX,
            "nyquist_cycles_per_mm": nyquist,
        },
        "sharpness": {
            "quantity": "processed-stock modulation transfer of spatial density changes",
            "fitted_mtf50_cycles_per_mm_rgb": [
                first_crossing(dense_frequencies, dense_response[:, channel], 0.5)
                for channel in range(3)
            ],
            "fitted_peak_response_percent_rgb": (
                np.max(dense_response, axis=0) * 100.0
            ).tolist(),
            "synthetic_edge_10_90_width_micrometres_rgb": edge_widths(),
            "official_graph_sample_audit": sample_rows,
            "all_broad_visual_envelopes_pass": every_sample_in_envelope,
        },
        "granularity": {
            "quantity": "standard deviation of local diffuse optical density",
            "kodak_aperture_diameter_micrometres": float(
                e.KODAK_GRANULARITY_APERTURE_DIAMETER_UM
            ),
            "aperture_diameter_pixels_at_native_width": aperture_pixels,
            "exposure_conditioned_sigma_d_rgb": e.GRANULARITY_SIGMA_D_RGB.tolist(),
        },
        "joint_interpretation": {
            "density_is_image_variable": True,
            "absolute_density_is_sharpness": False,
            "sharpness_requires_spatial_density_change": True,
            "grain_automatically_replaces_mtf": False,
            "model_decomposition": (
                "processed mean-density signal MTF plus a stochastic density residual "
                "whose 48-micrometre RMS and spatial morphology are calibrated on the "
                "same 24.9-mm image-width scale"
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
