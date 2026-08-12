#!/usr/bin/env python3
"""Audit withdrawal of the unmeasured continuous 2383 density shaper."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import time

import cv2
import numpy as np

import emulsion_experiment as e
import v63_profile
import v64_profile
from audit_v63_neutral_trajectory import difference_metrics


ENGINE = Path(__file__).resolve().parents[1]
V63_LATTICE = ENGINE / "cache/print_2383_monitor_output_lut_193_v63.npy"
V64_LATTICE = ENGINE / "cache/print_2383_monitor_output_lut_193_v64.npy"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def neutral_scene() -> tuple[np.ndarray, np.ndarray]:
    stops = np.linspace(-8.0, 6.0, 225, dtype=np.float32)
    scene = np.repeat((0.18 * np.power(2.0, stops))[:, None], 3, axis=1)
    return stops, scene.astype(np.float32)


def production_negative(scene: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    film = e.scene_to_5279_film_rgb(
        scene,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=False,
        sensor_noise_treatment="photochemical",
    )
    records = e.develop_5279_record_density(e.film_records_from_rgb(film))
    return records, e.negative_total_printer_density_from_record_density(records)


def pre_view_neutral_metrics(profile) -> dict[str, object]:
    profile.apply(e)
    stops, scene = neutral_scene()
    _records, negative = production_negative(scene)
    print_density = e.print_2383_density_from_negative(negative)
    projected = e.apply_2383_projection_lut(
        e.apply_2383_callier_density(print_density)
    )
    lab = e.linear_rec709_to_oklab(np.maximum(projected, 0.0))
    chroma = np.linalg.norm(lab[..., 1:3], axis=-1)
    mask = (lab[..., 0] > 0.01) & (lab[..., 0] < 0.99)
    lad_index = int(np.argmin(np.abs(stops + 0.45)))
    lad_status_a, _amounts = e.integral_status_a_from_2383_principal_density_rgb(
        print_density[lad_index]
    )
    return {
        "density_policy": e.PRINT_2383_DENSITY_NEUTRAL_POLICY,
        "pre_view_oklab_chroma_median": float(np.median(chroma[mask])),
        "pre_view_oklab_chroma_p95": float(np.percentile(chroma[mask], 95)),
        "pre_view_oklab_chroma_maximum": float(np.max(chroma[mask])),
        "nearest_lad_integral_status_a_rgb": lad_status_a.tolist(),
    }


def shaper_magnitude() -> dict[str, object]:
    v63_profile.apply(e)
    _stops, scene = neutral_scene()
    _records, negative = production_negative(scene)
    raw = e._raw_print_2383_density_from_negative(negative)
    shaped = e.print_2383_density_from_negative(negative)
    delta = shaped - raw
    return {
        "maximum_absolute_change_D_rgb": np.max(np.abs(delta), axis=0).tolist(),
        "rms_change_D_rgb": np.sqrt(np.mean(delta * delta, axis=0)).tolist(),
    }


def construction_path_gate() -> dict[str, object]:
    """Check the old calibration input against the actual production neutral path."""
    v63_profile.apply(e)
    stops = np.linspace(-10.0, 7.0, 273, dtype=np.float32)
    scene = np.repeat((0.18 * np.power(2.0, stops))[:, None], 3, axis=1)
    _records, production_negative_density = production_negative(scene)
    production_raw = e._raw_print_2383_density_from_negative(
        production_negative_density
    )
    shifted = np.repeat(
        (0.18 * np.power(2.0, stops + 0.45))[:, None], 3, axis=1
    ).astype(np.float32)
    construction_raw = e._raw_print_2383_density_from_negative(
        e.negative_total_printer_density(shifted)
    )
    absolute = np.abs(production_raw - construction_raw)
    return {
        "maximum_absolute_density_difference_D": float(np.max(absolute)),
        "mean_absolute_density_difference_D": float(np.mean(absolute)),
        "interpretation": (
            "The historical builder uses the complete active 5279 development "
            "path. Its simplified neutral film-light coordinate differs only "
            "slightly from the production camera-to-film path and is not the "
            "reason the continuous target lacks measurement authority."
        ),
    }


def lattice_archive_gate(samples: int = 128) -> dict[str, object]:
    v63_profile.apply(e)
    lattice = np.load(V63_LATTICE, mmap_mode="r")
    rng = np.random.default_rng(2383)
    index = rng.integers(0, lattice.shape[0], size=(samples, 3))
    axis = np.linspace(
        -0.16, e.NEGATIVE_5279_MAX_RECORD_DENSITY, lattice.shape[0], dtype=np.float32
    )
    total = np.stack(
        [axis[index[:, 0]], axis[index[:, 1]], axis[index[:, 2]]], axis=-1
    ) + e.SENSITO_DMIN_RGB
    direct = e.render_2383_monitor_projection_from_record_density(total)
    archived = np.asarray(lattice[index[:, 0], index[:, 1], index[:, 2]])
    return {
        "sampled_v63_native_nodes": samples,
        "exactly_equal": bool(np.array_equal(direct, archived)),
        "maximum_absolute_difference": float(np.max(np.abs(direct - archived))),
        "v63_lattice_sha256": sha256(V63_LATTICE),
        "v64_lattice_sha256": sha256(V64_LATTICE),
    }


def decode_reduced(source: Path, decoder: Path, frame: int, width: int, height: int) -> np.ndarray:
    payload = subprocess.check_output(
        [str(decoder), str(source), str(frame), "1"], stderr=subprocess.DEVNULL
    )
    expected = 5760 * 4320 * 3 * 4
    if len(payload) != expected:
        raise RuntimeError(f"decoder returned {len(payload)} bytes; expected {expected}")
    native = np.frombuffer(payload, dtype="<f4").reshape(4320, 5760, 3)
    reduced = cv2.resize(native, (width, height), interpolation=cv2.INTER_AREA)
    del native, payload
    gc.collect()
    return reduced.astype(np.float32)


def render(profile, raw: np.ndarray, authority: str) -> tuple[np.ndarray, np.ndarray]:
    profile.apply(e)
    e.PRINT_MONITOR_COLOUR_AUTHORITY = authority
    e.refresh_5279_spectral_observer_caches()
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    records = e.develop_5279_record_density(e.film_records_from_rgb(film))
    return (
        e.render_2383_monitor_projection_from_record_density(records),
        e.render_cineon_scan_master_from_record_density(records),
    )


def luma_metrics(image: np.ndarray) -> dict[str, float]:
    luma = np.einsum("...c,c->...", image, [0.2126, 0.7152, 0.0722])
    return {
        "p001": float(np.percentile(luma, 0.1)),
        "p01": float(np.percentile(luma, 1)),
        "median": float(np.median(luma)),
        "p99": float(np.percentile(luma, 99)),
        "p999": float(np.percentile(luma, 99.9)),
        "at_or_below_zero_fraction": float(np.mean(luma <= 0.0)),
        "at_or_above_one_fraction": float(np.mean(luma >= 1.0)),
    }


def real_frame_audit(
    source: Path, decoder: Path, frame: int, width: int, height: int
) -> dict[str, object]:
    started = time.perf_counter()
    raw = decode_reduced(source, decoder, frame, width, height)
    v63_scan_colour, v63_scan = render(v63_profile, raw, "scan_referenced_v31")
    v64_scan_colour, v64_scan = render(v64_profile, raw, "scan_referenced_v31")
    v63_physical, _ = render(v63_profile, raw, "physical_spectral_v56")
    v64_physical, _ = render(v64_profile, raw, "physical_spectral_v56")
    return {
        "source": str(source),
        "frame": frame,
        "working_dimensions": [width, height],
        "seconds": time.perf_counter() - started,
        "scan_branch_v63_vs_v64": difference_metrics(v63_scan, v64_scan),
        "scan_referenced_projection_v63_vs_v64": difference_metrics(
            v63_scan_colour, v64_scan_colour
        ),
        "physical_projection_v63_vs_v64": difference_metrics(
            v63_physical, v64_physical
        ),
        "luma": {
            "v63_scan_referenced_projection": luma_metrics(v63_scan_colour),
            "v64_scan_referenced_projection": luma_metrics(v64_scan_colour),
            "v63_physical_projection": luma_metrics(v63_physical),
            "v64_physical_projection": luma_metrics(v64_physical),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"
        ),
    )
    parser.add_argument("--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode"))
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--skip-real-frame", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {
        "audit": "V64 2383 density-neutral shaper ownership audit",
        "published_curve_interpretation": (
            "Kodak H-1-2383 identifies the sensitometric curves as response to "
            "red, green and blue light, exposed through Series 1700 filters, "
            "processed ECP-2D and measured by Status-A densitometry. The engine "
            "already inverts each separated Status-A response to analytical dye "
            "amount before combining the three vector-traced dye spectra."
        ),
        "construction_path": construction_path_gate(),
        "shaper_magnitude": shaper_magnitude(),
        "pre_view_neutral": {
            "v63_continuous_shaper": pre_view_neutral_metrics(v63_profile),
            "v64_published_curves": pre_view_neutral_metrics(v64_profile),
        },
        "archive_compatibility": lattice_archive_gate(),
        "decision": {
            "withdraw": (
                "continuous principal-density mean shaper: no measured off-LAD "
                "triplets identify its up-to-0.114 D curve rewrite"
            ),
            "retain": (
                "vector-traced Kodak separated Status-A H-D curves, analytical "
                "dye inversion, V63 actual view-neutral trajectory, scan colour "
                "authority and V62 identity interimage endpoint"
            ),
        },
    }
    if not args.skip_real_frame:
        report["real_frame"] = real_frame_audit(
            args.source, args.decoder, args.frame, args.width, args.height
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
