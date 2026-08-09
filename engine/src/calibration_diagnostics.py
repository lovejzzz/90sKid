#!/usr/bin/env python3
"""Generate step-wedge diagnostics for the 5279 -> 2383 print chain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import emulsion_experiment as emulsion


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    stops = np.linspace(-10.0, 8.0, 361, dtype=np.float32)
    reflection = 0.18 * np.power(2.0, stops)
    neutral = np.repeat(reflection[:, None], 3, axis=1).astype(np.float32)
    vgamut = emulsion.bt2020_to_panasonic_vgamut(neutral)
    film_rgb = emulsion.vgamut_to_balanced_film_rgb(vgamut)
    records = emulsion.film_records_from_rgb(film_rgb)
    net_densities = emulsion.record_densities(records) - emulsion.SENSITO_DMIN_RGB
    negative_density = emulsion.negative_total_printer_density(film_rgb)
    print_density = emulsion.print_2383_density_from_negative(negative_density)

    raster = neutral.reshape(1, neutral.shape[0], 3)
    print_linear = emulsion.render_to_display_linear(raster, look="print")[0]
    scan_linear = emulsion.render_to_display_linear(raster, look="cineon_scan")[0]
    print_2383_linear = emulsion.render_to_display_linear(raster, look="2383_projection")[0]
    print_luma = np.einsum("...c,c->...", print_linear, [0.2126, 0.7152, 0.0722])
    scan_luma = np.einsum("...c,c->...", scan_linear, [0.2126, 0.7152, 0.0722])
    print_2383_luma = np.einsum(
        "...c,c->...", print_2383_linear, [0.2126, 0.7152, 0.0722]
    )

    fig, axes = plt.subplots(2, 2, figsize=(13.0, 8.2), constrained_layout=True)
    colours = ("#d45757", "#57a66b", "#597fd1")
    labels = ("Red record / cyan dye", "Green record / magenta dye", "Blue record / yellow dye")
    for channel in range(3):
        axes[0, 0].plot(stops, negative_density[:, channel], color=colours[channel], label=labels[channel])
    axes[0, 0].set(title="5279 total printer density (orange mask retained)", xlabel="Stops from 18% gray", ylabel="Status-M density")
    axes[0, 0].grid(alpha=0.25)
    axes[0, 0].legend(fontsize=8)

    for channel in range(3):
        axes[0, 1].plot(stops, print_density[:, channel], color=colours[channel], label=labels[channel].split(" /")[0])
    axes[0, 1].axhline(1.0, color="black", ls="--", lw=0.8, label="LAD density 1.0")
    axes[0, 1].set(title="2383 Status-A density after optical printing", xlabel="Stops from 18% gray", ylabel="Print density")
    axes[0, 1].set_ylim(0, 4.2)
    axes[0, 1].grid(alpha=0.25)
    axes[0, 1].legend(fontsize=8)

    axes[1, 0].plot(stops, print_luma, label="v9 synthetic print", color="#ba6d32", alpha=0.75)
    axes[1, 0].plot(stops, print_2383_luma, label="v11 calibrated 2383 projection", color="#9a3f78")
    axes[1, 0].plot(stops, scan_luma, label="v11 Cineon / Spirit 2K scan", color="#397b9b")
    axes[1, 0].axhline(0.18, color="black", ls="--", lw=0.8)
    axes[1, 0].set(title="Display-linear viewing branches", xlabel="Stops from 18% gray", ylabel="Rec.709 linear luminance")
    axes[1, 0].set_ylim(0, 1.02)
    axes[1, 0].grid(alpha=0.25)
    axes[1, 0].legend()

    dye_colours = ("#45a4b4", "#c353a0", "#d3b638")
    for channel, (colour, label) in enumerate(zip(dye_colours, ("Cyan", "Magenta", "Yellow"), strict=True)):
        axes[1, 1].plot(
            emulsion.PRINT_DYE_WAVELENGTHS_NM,
            emulsion.PRINT_DYE_CMY_SPECTRAL_DENSITY[:, channel],
            color=colour,
            label=label,
        )
    axes[1, 1].set(title="2383 dye spectral-density model", xlabel="Wavelength (nm)", ylabel="Relative diffuse density")
    axes[1, 1].grid(alpha=0.25)
    axes[1, 1].legend()

    fig.suptitle("Kodak 5279 v11 colour paths: calibrated 2383 projection and Cineon scan", fontsize=14)
    fig.savefig(args.output_dir / "v11_colour_path_diagnostics.png", dpi=180)
    plt.close(fig)

    sample_stops = np.array([-8, -6, -4, -2, 0, 2, 4, 6], dtype=np.float32)
    indices = [int(np.argmin(np.abs(stops - value))) for value in sample_stops]
    document = {
        "vlog_18_percent": float(emulsion.vlog_encode(np.array(0.18, dtype=np.float32))),
        "sensitometric_sources": [
            "Kodak H-1-5279t visual digitization",
            "Kodak H-1-2383 (revised 3-26) visual digitization",
        ],
        "print_lad_density": emulsion.PRINT_2383_LAD_DENSITY,
        "projection_model": "21 wavelength samples, 380-780 nm, 5600 K xenon-like illuminant",
        "neutral_calibration": "multi-step Status-M -> Status-A gray scale plus projected gray-scale shaper",
        "scan_model": "Spirit 2K inspired; Cineon reference black 95, gray 445, 0.002 density/code",
        "samples": [
            {
                "stops_from_18_percent": float(stops[index]),
                "negative_net_density_rgb_records": [float(value) for value in net_densities[index]],
                "negative_total_printer_density_rgb": [float(value) for value in negative_density[index]],
                "print_2383_density_rgb": [float(value) for value in print_density[index]],
                "synthetic_print_linear_luma": float(print_luma[index]),
                "print_2383_linear_luma": float(print_2383_luma[index]),
                "cineon_scan_linear_luma": float(scan_luma[index]),
            }
            for index in indices
        ],
    }
    (args.output_dir / "v11_colour_path_diagnostics.json").write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
