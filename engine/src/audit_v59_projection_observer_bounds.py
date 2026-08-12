#!/usr/bin/env python3
"""Bound 2383 colour uncertainty caused by the unmeasured theatre observer.

Kodak's Essential Reference Guide publishes a generic xenon-lamp relative
spectral-energy graph.  It is not a measurement of one projector's lamp,
heat glass, lens and screen.  This audit freezes V58's 5279 and 2383 image
formation, varies only the viewing spectral power distribution, adapts each
open-gate white to D65, and reports the remaining metameric colour interval.

The 5400 K and 6420 K spectra are Planckian *brackets*, not claims that a xenon
arc is a black body.  Equal energy is included because Kodak's 2383 hard-dye
patent uses it to define one analytical-dye normalization; it is likewise not
a theatre-viewing claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v59_profile


def _bradford(source_white_xyz: np.ndarray) -> np.ndarray:
    matrix = np.asarray(
        [
            [0.8951, 0.2664, -0.1614],
            [-0.7502, 1.7135, 0.0367],
            [0.0389, -0.0685, 1.0296],
        ],
        dtype=np.float64,
    )
    destination = np.asarray([0.95047, 1.0, 1.08883], dtype=np.float64)
    source = source_white_xyz / source_white_xyz[1]
    return (
        np.linalg.inv(matrix)
        @ np.diag((matrix @ destination) / (matrix @ source))
        @ matrix
    )


def _observe(
    principal_density_rgb: np.ndarray,
    illuminant: np.ndarray,
) -> np.ndarray:
    wavelength, cmf = e._cie_1931_xyz_official_1nm()
    graph_wavelength = np.asarray(e.PRINT_DYE_WAVELENGTHS_NM, dtype=np.float64)
    dye = np.stack(
        [
            np.interp(
                wavelength,
                graph_wavelength,
                e.PRINT_DYE_CMY_SPECTRAL_DENSITY[:, channel],
            )
            for channel in range(3)
        ],
        axis=1,
    )
    base = np.interp(
        wavelength,
        graph_wavelength,
        e.PRINT_2383_DMIN_SPECTRAL_DENSITY,
    )
    weights = np.ones(wavelength.size, dtype=np.float64)
    weights[[0, -1]] = 0.5
    weighted_cmf = illuminant[:, None] * cmf * weights[:, None]
    white_xyz = np.sum(weighted_cmf, axis=0)
    adaptation = _bradford(white_xyz)

    density = np.asarray(principal_density_rgb, dtype=np.float32)
    axes = e._print_2383_analytical_amount_axes(
        np.linspace(0.0, e.PRINT_2383_DMAX, 28001, dtype=np.float32)
    )
    amount = np.stack(
        [
            np.interp(
                density[..., channel],
                np.linspace(0.0, e.PRINT_2383_DMAX, 28001),
                axes[channel],
            )
            for channel in range(3)
        ],
        axis=-1,
    )
    # Some Accelerate/OpenBLAS builds spuriously raise floating-point status
    # flags for these finite matrix products. Bound the values explicitly and
    # reject any real non-finite result after the operation.
    with np.errstate(all="ignore"):
        spectral_density = np.clip(
            amount.reshape(-1, 3) @ dye.T + base[None, :], 0.0, 20.0
        )
        transmission = np.power(10.0, -spectral_density)
        xyz = transmission @ weighted_cmf
        xyz /= white_xyz[1]
        xyz = xyz @ adaptation.T
        rgb = xyz @ np.asarray(e.XYZ_D65_TO_REC709, dtype=np.float64).T
    if not np.all(np.isfinite(rgb)):
        raise RuntimeError("projection observer produced non-finite RGB")
    return rgb.reshape(density.shape).astype(np.float64)


def _xy(rgb: np.ndarray) -> list[float]:
    xyz = np.asarray(rgb, dtype=np.float64) @ np.linalg.inv(
        np.asarray(e.XYZ_D65_TO_REC709, dtype=np.float64)
    ).T
    denominator = float(np.sum(xyz))
    return [float(xyz[0] / denominator), float(xyz[1] / denominator)]


def measure(cube_size: int) -> dict[str, object]:
    if cube_size < 5:
        raise ValueError("cube size must be at least five")
    v59_profile.apply(e)
    wavelength, _cmf = e._cie_1931_xyz_official_1nm()
    spds = {
        "kodak_generic_xenon_graph": np.interp(
            wavelength,
            e.PRINT_DYE_WAVELENGTHS_NM,
            e.KODAK_XENON_PROJECTOR_RELATIVE_SPD,
        ),
        "planck_5400k_measurement_proxy": e._blackbody_spd(wavelength, 5400.0),
        "planck_6420k_xenon_cct_proxy": e._blackbody_spd(wavelength, 6420.0),
        "equal_energy_patent_reference": np.ones_like(wavelength),
    }

    axis = np.linspace(0.0, e.PRINT_2383_DMAX, cube_size, dtype=np.float32)
    red, green, blue = np.meshgrid(axis, axis, axis, indexing="ij")
    cube = np.stack([red, green, blue], axis=-1)
    lad = np.asarray(e.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB, dtype=np.float32)
    samples = np.concatenate(
        [
            cube.reshape(-1, 3),
            lad[None, :],
            np.diag(np.full(3, 1.0, dtype=np.float32)),
        ],
        axis=0,
    )
    observations = {name: _observe(samples, spd) for name, spd in spds.items()}
    reference = observations["kodak_generic_xenon_graph"]
    reference_lab = e.linear_rec709_to_oklab(reference.astype(np.float32))
    cube_count = cube_size**3

    comparisons: dict[str, object] = {}
    for name, rgb in observations.items():
        lab = e.linear_rec709_to_oklab(rgb.astype(np.float32))
        delta = 100.0 * np.linalg.norm(lab - reference_lab, axis=-1)
        comparisons[name] = {
            "oklab_delta_e_vs_generic_xenon_cube": {
                "median": float(np.median(delta[:cube_count])),
                "p95": float(np.percentile(delta[:cube_count], 95.0)),
                "maximum": float(np.max(delta[:cube_count])),
            },
            "raw_lad_linear_rec709": rgb[cube_count].tolist(),
            "raw_lad_xy": _xy(rgb[cube_count]),
            "one_density_separation_linear_rec709": rgb[
                cube_count + 1 : cube_count + 4
            ].tolist(),
        }

    return {
        "audit": "V59 2383 projection-observer spectral bounds",
        "image_change": "none",
        "profile": v59_profile.PROFILE["name"],
        "frozen": (
            "V59 5279 formation, 2383 H-D, sensitivity, dye/base spectra, LAD "
            "coordinate, CIE observer and Bradford adaptation"
        ),
        "varied_only": "viewing spectral power distribution",
        "cube": {
            "size": cube_size,
            "principal_density_min": 0.0,
            "principal_density_max": float(e.PRINT_2383_DMAX),
            "sample_count": cube_count,
        },
        "comparisons": comparisons,
        "interpretation_boundary": (
            "The interval is observer metamerism under white-adapted spectral "
            "brackets. It does not identify a historical theatre because no "
            "lamp/heat-glass/lens/screen SPD was measured."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cube-size", type=int, default=17)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = measure(args.cube_size)
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
