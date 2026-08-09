#!/usr/bin/env python3
"""Build and validate a white-point-robust V23 monitor-colour lattice."""

from __future__ import annotations

import gc
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VENDOR_DIR = ROOT / "research_runs" / "2026-08-03_vendor_2383_targets"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(VENDOR_DIR))
import emulsion_experiment as e  # noqa: E402
import run_cross_vendor_holdout as cross  # noqa: E402
import run_real_frame_vendor_ab as va  # noqa: E402
from analyze_vendor_luts import SOURCES, load_cube, neutral_for_output, sample_3d  # noqa: E402

DECODER = Path("/tmp/prores_raw_float_decode")
CASES = [
    (Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T002.MOV"), [12]),
    (Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T020.MOV"), [0, 36, 71]),
    (Path("/Users/tianxing/Movies/test-proresRawlog/NJARAW_S001_S001_T032.MOV"), [0, 36, 71]),
]
LUT_PATH = HERE / "v23_resolve_triad_relative_chroma_lut_25.npz"
METRICS_PATH = HERE / "v23_colour_candidate_metrics.json"


def build_triad_lut(size: int = 25) -> np.ndarray:
    net_min, net_max = -0.16, e.NEGATIVE_5279_MAX_RECORD_DENSITY
    axis = np.linspace(net_min, net_max, size, dtype=np.float32)
    red, green, blue = np.meshgrid(axis, axis, axis, indexing="ij")
    total = np.stack([red, green, blue], axis=-1) + e.SENSITO_DMIN_RGB
    candidate = e._render_2383_monitor_projection_base_from_record_density(total)
    cineon = va.continuous_cineon_image(e, total)
    neutral = np.repeat(np.mean(cineon, axis=-1, keepdims=True), 3, axis=-1)
    relative_vectors = []
    for white in ("d55", "d60", "d65"):
        cube = load_cube(SOURCES[f"resolve_rec709_{white}"])
        colour_lab = e.linear_rec709_to_oklab(
            va.gamma24_decode(va.sample_cube_image(cube, cineon))
        )
        neutral_lab = e.linear_rec709_to_oklab(
            va.gamma24_decode(va.sample_cube_image(cube, neutral))
        )
        relative_vectors.append(colour_lab[..., 1:3] - neutral_lab[..., 1:3])
    target_ab = 0.99 * np.median(np.stack(relative_vectors), axis=0)
    candidate_lab = e.linear_rec709_to_oklab(candidate)
    code_chroma = np.max(cineon, axis=-1) - np.min(cineon, axis=-1)
    guard = e.smoothstep(0.008, 0.040, code_chroma)
    target_lab = candidate_lab.copy()
    target_lab[..., 1:3] = (
        candidate_lab[..., 1:3] * (1.0 - guard[..., None])
        + target_ab * guard[..., None]
    )
    return (target_lab - candidate_lab).astype(np.float32)


def apply_lut(total: np.ndarray, lut: np.ndarray) -> np.ndarray:
    base = e._render_2383_monitor_projection_base_from_record_density(total)
    delta = va.sample_density_lut(e, lut, total)
    cineon = va.continuous_cineon_image(e, total)
    guard = e.smoothstep(0.008, 0.040, np.max(cineon, axis=-1) - np.min(cineon, axis=-1))
    lab = e.linear_rec709_to_oklab(base)
    lab += delta * guard[..., None]
    return np.clip(e.compress_oklab_chroma_to_rec709(e.oklab_to_linear_rec709(lab)), 0.0, 1.0)


def decode(path: Path, frame: int) -> np.ndarray:
    width, height, _ = e.probe_video(path)
    result = subprocess.run(
        [str(DECODER), str(path), str(frame), "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    native = np.frombuffer(result.stdout, dtype="<f4").reshape(height, width, 3)
    return cv2.resize(native, (1440, 1080), interpolation=cv2.INTER_AREA).astype(np.float32)


def density_from_raw(raw: np.ndarray) -> np.ndarray:
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    return e.develop_5279_record_density(e.film_records_from_rgb(film))


def save(path: Path, linear: np.ndarray) -> None:
    encoded = e.srgb_encode(np.clip(linear, 0.0, 1.0))
    image = np.rint(encoded * 255.0).astype(np.uint8)
    cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])


def finite_colour_metrics(lut: np.ndarray) -> dict[str, object]:
    cross.install_candidate()
    ce = cross.candidate
    neutral_total = cross.neutral_record_density(ce)
    neutral_q = cross.continuous_cineon_code(ce, neutral_total)
    delta = 0.060
    directions = {
        "red": np.array([delta, -delta / 2, -delta / 2]),
        "cyan": np.array([-delta, delta / 2, delta / 2]),
        "green": np.array([-delta / 2, delta, -delta / 2]),
        "magenta": np.array([delta / 2, -delta, delta / 2]),
        "blue": np.array([-delta / 2, -delta / 2, delta]),
        "yellow": np.array([delta / 2, delta / 2, -delta]),
    }
    totals = {name: cross.solve_total_for_cineon(ce, neutral_q + vector, neutral_total) for name, vector in directions.items()}
    vendor_names = [
        "resolve_rec709_d55", "resolve_rec709_d60", "resolve_rec709_d65",
        "adobe_5218_2383", "filmvision_sd1", "filmvision_sd2", "filmvision_sd3",
    ]
    vendor_angles: dict[str, dict[str, float]] = {}
    vendor_magnitudes: dict[str, dict[str, float]] = {}
    for vendor in vendor_names:
        cube = load_cube(SOURCES[vendor])
        fn = lambda value, cube=cube: sample_3d(cube, value)
        center = neutral_for_output(fn, 0.50)
        gamma = 2.2 if vendor.startswith("adobe") else 2.4
        neutral = cross.rec709_decode(fn(np.full(3, center)), gamma)
        vendor_angles[vendor], vendor_magnitudes[vendor] = {}, {}
        for name, vector in directions.items():
            ab = cross.delta_ab(ce, cross.rec709_decode(fn(np.full(3, center) + vector), gamma), neutral)
            vendor_angles[vendor][name] = cross.angle_degrees(ab)
            vendor_magnitudes[vendor][name] = float(np.linalg.norm(ab))
    consensus = {name: cross.circular_median([vendor_angles[v][name] for v in vendor_names]) for name in directions}

    old_lut = e.load_2383_d60_relative_chroma_delta_lut()
    rows: dict[str, object] = {}
    for renderer_name, lattice in (("v22_d60", old_lut), ("v23_triad", lut)):
        neutral = apply_lut(neutral_total[None, None], lattice)[0, 0]
        errors, magnitudes, patches = [], [], {}
        for name, total in totals.items():
            output = apply_lut(total[None, None], lattice)[0, 0]
            ab = cross.delta_ab(ce, output, neutral)
            error = cross.angular_distance(cross.angle_degrees(ab), consensus[name])
            magnitude = float(np.linalg.norm(ab))
            vendor_range = [vendor_magnitudes[v][name] for v in vendor_names]
            errors.append(error)
            magnitudes.append(magnitude)
            patches[name] = {"hue_error_degrees": error, "magnitude": magnitude, "inside_vendor_magnitude_envelope": bool(min(vendor_range) <= magnitude <= max(vendor_range))}
        rows[renderer_name] = {
            "mean_hue_error_degrees": float(np.mean(errors)),
            "median_hue_error_degrees": float(np.median(errors)),
            "maximum_hue_error_degrees": float(np.max(errors)),
            "all_magnitudes_inside_vendor_envelope": bool(all(row["inside_vendor_magnitude_envelope"] for row in patches.values())),
            "patches": patches,
        }
    return rows


def main() -> None:
    lut = build_triad_lut()
    np.savez_compressed(
        LUT_PATH,
        delta_oklab=lut,
        net_density_min=np.float32(-0.16),
        net_density_max=np.float32(e.NEGATIVE_5279_MAX_RECORD_DENSITY),
        target=np.array("componentwise median of neutral-subtracted Resolve D55/D60/D65 Oklab a/b"),
    )
    cubes = {name: load_cube(SOURCES[f"resolve_rec709_{name}"]) for name in ("d55", "d60", "d65")}
    report: dict[str, object] = {"finite_colours": finite_colour_metrics(lut), "real_frames": {}}
    for raw_path, frames in CASES:
        clip = raw_path.stem.split("_")[-1].lower()
        report["real_frames"][clip] = {}
        for frame in frames:
            density = density_from_raw(decode(raw_path, frame))
            cineon = va.continuous_cineon_image(e, density)
            vendors = {name: va.gamma24_decode(va.sample_cube_image(cube, cineon)) for name, cube in cubes.items()}
            v22 = e.render_2383_monitor_projection_from_record_density(density)
            v23 = apply_lut(density, lut)
            report["real_frames"][clip][str(frame)] = {
                "v22": va.bracket_membership(e, v22, vendors),
                "v23": va.bracket_membership(e, v23, vendors),
            }
            if frame == frames[len(frames) // 2]:
                save(HERE / f"{clip}_f{frame:03d}_v22.jpg", v22)
                save(HERE / f"{clip}_f{frame:03d}_v23.jpg", v23)
            del density, cineon, vendors, v22, v23
            gc.collect()
    METRICS_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
