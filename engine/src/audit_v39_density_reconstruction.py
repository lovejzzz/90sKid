#!/usr/bin/env python3
"""Independent structural gates for the V39 density-formation release."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v38_profile
import v39_profile


def decode_frame(decoder: Path, source: Path, frame: int) -> np.ndarray:
    width, height, _ = e.probe_video(source)
    payload = subprocess.check_output(
        [str(decoder), str(source), str(frame), "1"],
        stderr=subprocess.DEVNULL,
    )
    expected = width * height * 3 * 4
    if len(payload) != expected:
        raise RuntimeError(f"decoder returned {len(payload)} bytes, expected {expected}")
    return np.frombuffer(payload, dtype="<f4").reshape(height, width, 3)


def rms(values: np.ndarray) -> np.ndarray:
    return np.std(values, axis=(0, 1)).astype(np.float64)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoder", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {
        "release": v39_profile.PROFILE["name"],
        "gates": {},
    }
    gates: dict[str, object] = report["gates"]  # type: ignore[assignment]

    v39_profile.apply(e)
    v39_flags = {
        "film_basis_preclip": e.FILM_RGB_CLIP_BEFORE_RECORDS,
        "grain_calibration_domain": e.GRAIN_CALIBRATION_DOMAIN,
        "image_structure_domain": e.IMAGE_STRUCTURE_DOMAIN,
        "print_grain_domain": e.PRINT_GRAIN_DOMAIN,
        "subpixel_radius": e.GRAIN_SUBPIXEL_PHASE_RADIUS_PX,
    }
    v38_profile.apply(e)
    v38_reset = {
        "film_basis_preclip": e.FILM_RGB_CLIP_BEFORE_RECORDS,
        "grain_calibration_domain": e.GRAIN_CALIBRATION_DOMAIN,
        "image_structure_domain": e.IMAGE_STRUCTURE_DOMAIN,
        "print_grain_domain": e.PRINT_GRAIN_DOMAIN,
    }
    gates["profile_source_of_truth"] = {
        "pass": (
            v39_flags["film_basis_preclip"] is False
            and v39_flags["grain_calibration_domain"] == "pre_dir_dye_yield"
            and v39_flags["image_structure_domain"] == "formed_density"
            and v39_flags["print_grain_domain"] == "print_density"
            and v38_reset["film_basis_preclip"] is True
            and v38_reset["grain_calibration_domain"]
            == "post_coupling_residual"
        ),
        "v39": v39_flags,
        "v38_after_v39": v38_reset,
    }

    v39_profile.apply(e)
    height, width = 192, 320
    scene = np.full((height, width, 3), 0.18, dtype=np.float32)
    records = e.film_records_from_rgb(scene)
    mean_density = e.develop_5279_record_density(records)
    formed_density = e.form_5279_multilayer_record_density(
        records, 393, 1.0, 1
    )
    target = np.mean(
        e.published_5279_granularity_sigma(
            np.log10(np.maximum(records, 1e-8)) - 1.0
        ),
        axis=(0, 1),
    ).astype(np.float64)
    measured = rms(formed_density - mean_density)
    relative_error = np.abs(measured - target) / np.maximum(target, 1e-12)
    gates["kodak_48um_rms_midgray"] = {
        "pass": bool(np.all(relative_error < 0.01)),
        "measured_density_rms_rgb": measured.tolist(),
        "target_density_rms_rgb": target.tolist(),
        "relative_error_rgb": relative_error.tolist(),
        "tolerance": 0.01,
    }

    rng = np.random.default_rng(39)
    total = (
        e.SENSITO_DMIN_RGB
        + rng.random((32, 48, 3), dtype=np.float32) * 2.5
    )
    print_density = e.print_2383_density_from_negative(
        e.negative_total_printer_density_from_record_density(total)
    )
    legacy_entry = e._render_2383_projection_uncalibrated(total)
    density_entry = e._render_2383_projection_uncalibrated_from_print_density(
        print_density
    )
    entry_error = float(np.max(np.abs(legacy_entry - density_entry)))
    gates["2383_density_entry_equivalence"] = {
        "pass": entry_error == 0.0,
        "maximum_absolute_error": entry_error,
    }

    deterministic_print = np.full((256, 256, 3), 1.0, dtype=np.float32)
    grained_print = e.form_2383_fine_grain_density(
        deterministic_print, 39, 1.0
    )
    print_delta = grained_print - deterministic_print
    print_bias = np.mean(print_delta, axis=(0, 1)).astype(np.float64)
    gates["2383_density_grain"] = {
        "pass": bool(np.all(np.abs(print_bias) < 1e-4)),
        "mean_density_bias_rgb": print_bias.tolist(),
        "density_rms_rgb": rms(print_delta).tolist(),
        "domain": "2383 Status-A density before projection",
    }

    if args.decoder is not None and args.source is not None:
        raw = decode_frame(args.decoder, args.source, args.frame)
        v38_profile.apply(e)
        old_basis = e.scene_to_5279_film_rgb(
            raw,
            0.45,
            raw_colour=v38_profile.PROFILE["raw_colour"],
            include_optical_scatter=False,
            sensor_noise_treatment="photochemical",
        )
        old_records = e.film_records_from_rgb(old_basis)
        v39_profile.apply(e)
        signed_basis = e.scene_to_5279_film_rgb(
            raw,
            0.45,
            raw_colour=v39_profile.PROFILE["raw_colour"],
            include_optical_scatter=False,
            sensor_noise_treatment="photochemical",
        )
        new_records = e.film_records_from_rgb(signed_basis)
        affected = np.any(old_records != new_records, axis=-1)
        gates["raw_record_boundary"] = {
            "pass": bool(np.min(new_records) >= 0.0),
            "signed_basis_component_fraction": float(np.mean(signed_basis < 0.0)),
            "affected_pixel_fraction": float(np.mean(affected)),
            "minimum_physical_record": float(np.min(new_records)),
            "maximum_record_delta": float(
                np.max(np.abs(new_records - old_records))
            ),
        }

    report["all_gates_pass"] = all(
        bool(value["pass"])
        for value in gates.values()
        if isinstance(value, dict) and "pass" in value
    )
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
