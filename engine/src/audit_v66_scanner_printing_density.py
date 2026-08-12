#!/usr/bin/env python3
"""Audit the Spirit/Cineon correction target against printing density.

Kodak EP1309188A2 defines a data-scan calibration whose output code represents
the printing density seen by a specified printer lamp and target print stock.
The historical engine instead blends the broad telecine observation toward
independent Status-M record densities. This script compares those coordinates
without selecting a release look.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Callable

import cv2
import numpy as np

import emulsion_experiment as e
import v64_profile
from audit_v63_neutral_trajectory import difference_metrics
from audit_v63_neutral_trajectory import output_chart_diagnostic
from audit_v64_2383_density_shaper import decode_reduced, luma_metrics


DensityModel = Callable[[np.ndarray], np.ndarray]
T003_AUDIT = (
    Path(__file__).resolve().parents[1]
    / "research_runs/2026-08-06_t003_colorchecker/frame160_audit/"
    "t003_dkc_pro_audit.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def total_record_density_from_scene(scene: np.ndarray) -> np.ndarray:
    return e.develop_5279_record_density(e.film_records_from_rgb(scene))


def raw_period_density(total: np.ndarray) -> np.ndarray:
    signed = np.asarray(total, dtype=np.float32) - e.SENSITO_DMIN_RGB
    return e.apply_5279_net_density_lut(np.maximum(signed, 0.0))


def printing_net_density(total: np.ndarray) -> np.ndarray:
    base = e.negative_total_printer_density_from_record_density(
        e.SENSITO_DMIN_RGB
    )
    return (
        e.negative_total_printer_density_from_record_density(total) - base
    ).astype(np.float32)


def blended_density(
    total: np.ndarray, target: str, strength_mode: str
) -> np.ndarray:
    total = np.asarray(total, dtype=np.float32)
    signed = total - e.SENSITO_DMIN_RGB
    optical = raw_period_density(total)
    if target == "status_m_records":
        correction_target = signed
    elif target == "printing_density":
        correction_target = printing_net_density(total)
    else:
        raise ValueError(target)
    if strength_mode == "full":
        strength = np.ones(signed.shape[:-1], dtype=np.float32)
    elif strength_mode == "archive_82pct_with_shoulder_release":
        shoulder = e.smoothstep(
            float(e.SPIRIT_PRIMARY_CORRECTION_SHOULDER_DENSITY[0]),
            float(e.SPIRIT_PRIMARY_CORRECTION_SHOULDER_DENSITY[1]),
            np.mean(np.maximum(signed, 0.0), axis=-1),
        )
        strength = (
            e.SPIRIT_PRIMARY_CORRECTION_STRENGTH
            - e.SPIRIT_PRIMARY_CORRECTION_SHOULDER_RELEASE * shoulder
        ).astype(np.float32)
    else:
        raise ValueError(strength_mode)
    return (
        optical + strength[..., None] * (correction_target - optical)
    ).astype(np.float32)


def build_models() -> dict[str, DensityModel]:
    return {
        "v64_current_82pct_status_m": e.scanner_density_from_total_record_density,
        "raw_period_observer": raw_period_density,
        "full_status_m_records": lambda total: blended_density(
            total, "status_m_records", "full"
        ),
        "partial_printing_density": lambda total: blended_density(
            total, "printing_density", "archive_82pct_with_shoulder_release"
        ),
        "full_printing_density": printing_net_density,
    }


def neutral_anchors(model: DensityModel) -> tuple[np.ndarray, np.ndarray]:
    mid = total_record_density_from_scene(
        np.array([0.18, 0.18, 0.18], dtype=np.float32)
    )
    high = total_record_density_from_scene(
        np.array([10.0, 10.0, 10.0], dtype=np.float32)
    )
    return model(mid), model(high)


def cineon_display(
    scanner_density: np.ndarray,
    mid_density: np.ndarray,
    high_density: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    gain = np.float32(0.700) / np.maximum(mid_density, 1e-6)
    matched = np.asarray(scanner_density, dtype=np.float32) * gain
    code_unclipped = 95.0 + matched / 0.002
    code = np.clip(np.rint(code_unclipped), 0.0, 1023.0)
    decoded = (code - 95.0) * 0.002
    toe_width = 0.008
    decoded = 0.5 * (decoded + np.sqrt(decoded * decoded + toe_width**2))
    scaled_high = high_density * gain
    high_toe = 0.5 * (
        scaled_high + np.sqrt(scaled_high * scaled_high + toe_width**2)
    )
    mid_toe = 0.5 * (
        np.float32(0.700)
        + math.sqrt(np.float32(0.700) ** 2 + toe_width**2)
    )
    unit = decoded / np.maximum(high_toe, 1e-6)
    neutral_mid_unit = mid_toe / np.maximum(high_toe, 1e-6)
    peak = np.array([0.90, 0.90, 0.90], dtype=np.float32)
    power = np.log(0.18 / peak) / np.log(
        np.maximum(neutral_mid_unit, 1e-5)
    )
    mapped = peak * np.power(np.clip(unit, 0.0, 1.25), power)
    return e.compress_unit_gamut(mapped).astype(np.float32), code_unclipped


def finish_bluray(scan: np.ndarray) -> np.ndarray:
    return e.finish_cineon_scan_for_bluray(scan)


def build_neutral_table(
    model: DensityModel, mid: np.ndarray, high: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    levels = np.concatenate(
        [
            np.zeros(1, dtype=np.float32),
            np.geomspace(1e-5, 10.0, 1024, dtype=np.float32),
        ]
    )
    scene = np.repeat(levels[:, None], 3, axis=1)
    density = model(total_record_density_from_scene(scene))
    display, _code = cineon_display(density, mid, high)
    finished = finish_bluray(display)
    luma = np.einsum(
        "...c,c->...", np.maximum(finished, 0.0), [0.2126, 0.7152, 0.0722]
    ).astype(np.float32)
    factors = np.clip(
        luma[:, None] / np.maximum(finished, 1e-8), 0.35, 2.50
    )
    order = np.argsort(luma, kind="stable")
    luma = luma[order]
    factors = factors[order]
    unique, first, counts = np.unique(
        luma, return_index=True, return_counts=True
    )
    averaged = np.add.reduceat(factors, first, axis=0) / counts[:, None]
    if unique[0] > 0.0:
        unique = np.concatenate([np.zeros(1, dtype=np.float32), unique])
        averaged = np.concatenate(
            [np.ones((1, 3), dtype=np.float32), averaged], axis=0
        )
    if unique[-1] < 1.0:
        unique = np.concatenate([unique, np.ones(1, dtype=np.float32)])
        averaged = np.concatenate(
            [averaged, np.ones((1, 3), dtype=np.float32)], axis=0
        )
    return unique.astype(np.float32), averaged.astype(np.float32)


def apply_neutral_table(
    display: np.ndarray, table: tuple[np.ndarray, np.ndarray]
) -> np.ndarray:
    source = np.clip(np.asarray(display, dtype=np.float32), 0.0, 1.0)
    weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    luma = np.einsum("...c,c->...", source, weights)
    axis, factors = table
    corrected = np.empty_like(source)
    for channel in range(3):
        corrected[..., channel] = source[..., channel] * np.interp(
            luma, axis, factors[:, channel]
        ).astype(np.float32)
    corrected_luma = np.einsum("...c,c->...", corrected, weights)
    corrected *= (luma / np.maximum(corrected_luma, 1e-8))[..., None]
    corrected = np.where((luma > 0.0)[..., None], corrected, 0.0)
    return e.compress_unit_gamut(corrected).astype(np.float32)


def render_model(
    model: DensityModel, total: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mid, high = neutral_anchors(model)
    scanner_density = model(total)
    scan, code = cineon_display(scanner_density, mid, high)
    finished = finish_bluray(scan)
    table = build_neutral_table(model, mid, high)
    return apply_neutral_table(finished, table), code, mid, high


def density_target_metrics(models: dict[str, DensityModel]) -> dict[str, object]:
    axis = np.linspace(
        0.0, e.NEGATIVE_5279_MAX_RECORD_DENSITY, 17, dtype=np.float32
    )
    r, g, b = np.meshgrid(axis, axis, axis, indexing="ij")
    total = np.stack([r, g, b], axis=-1) + e.SENSITO_DMIN_RGB
    reference = printing_net_density(total)
    reference_mid, _ = neutral_anchors(printing_net_density)
    reference_scaled = reference * (
        np.float32(0.700) / np.maximum(reference_mid, 1e-6)
    )
    result: dict[str, object] = {}
    for name, model in models.items():
        density = model(total)
        mid, _high = neutral_anchors(model)
        scaled = density * (np.float32(0.700) / np.maximum(mid, 1e-6))
        delta = scaled - reference_scaled
        absolute = np.abs(delta)
        result[name] = {
            "rms_D": float(np.sqrt(np.mean(delta * delta))),
            "mae_D": float(np.mean(absolute)),
            "p95_absolute_D": float(np.percentile(absolute, 95)),
            "maximum_absolute_D": float(np.max(absolute)),
        }
    return result


def code_metrics(code: np.ndarray) -> dict[str, float]:
    return {
        "minimum_unclipped": float(np.min(code)),
        "p001_unclipped": float(np.percentile(code, 0.1)),
        "median_unclipped": float(np.median(code)),
        "p999_unclipped": float(np.percentile(code, 99.9)),
        "maximum_unclipped": float(np.max(code)),
        "below_zero_fraction": float(np.mean(code < 0.0)),
        "above_1023_fraction": float(np.mean(code > 1023.0)),
    }


def chart_diagnostic(models: dict[str, DensityModel]) -> dict[str, object]:
    document = json.loads(T003_AUDIT.read_text(encoding="utf-8"))
    scene = np.asarray(
        [row["decoded_linear_bt2020_median"] for row in document["patches"]],
        dtype=np.float32,
    )
    reference = np.asarray(
        [row["manufacturer_CIELAB_as_published"] for row in document["patches"]],
        dtype=np.float64,
    )
    film = e.scene_to_5279_film_rgb(
        scene,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=False,
        sensor_noise_treatment="photochemical",
    )
    total = e.develop_5279_record_density(e.film_records_from_rgb(film))
    result = {}
    for name, model in models.items():
        image, _code, _mid, _high = render_model(model, total)
        result[name] = output_chart_diagnostic(image, reference)
    return {
        "source": str(T003_AUDIT),
        "models": result,
        "authority": (
            "diagnostic only: scene SPD and manufacturer Lab reference "
            "illuminant/observer remain unidentified"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "/Users/tianxing/Movies/test-proresRawlog/"
            "NJARAW_S001_S001_T020.MOV"
        ),
    )
    parser.add_argument(
        "--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode")
    )
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("engine/research_runs/v66_scanner_printing_density_stills"),
    )
    args = parser.parse_args()

    started = time.perf_counter()
    v64_profile.apply(e)
    models = build_models()
    density_gate = density_target_metrics(models)
    chart_gate = chart_diagnostic(models)

    raw = decode_reduced(
        args.source, args.decoder, args.frame, args.width, args.height
    )
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    total = e.develop_5279_record_density(e.film_records_from_rgb(film))

    rendered: dict[str, np.ndarray] = {}
    codes: dict[str, np.ndarray] = {}
    anchors: dict[str, object] = {}
    for name, model in models.items():
        image, code, mid, high = render_model(model, total)
        rendered[name] = image
        codes[name] = code
        anchors[name] = {
            "neutral_mid_scanner_density": mid.tolist(),
            "neutral_high_scanner_density": high.tolist(),
        }

    args.image_dir.mkdir(parents=True, exist_ok=True)
    for name, image in rendered.items():
        signal = e.srgb_encode(np.clip(image, 0.0, 1.0))
        payload = np.rint(signal[..., ::-1] * 65535.0).astype(np.uint16)
        if not cv2.imwrite(str(args.image_dir / f"{name}.png"), payload):
            raise RuntimeError(f"failed to write {name} diagnostic")

    baseline = rendered["v64_current_82pct_status_m"]
    result = {
        "audit": "V66 scanner printing-density coordinate audit",
        "status": "profile_selected_full_printing_density",
        "source": str(args.source),
        "frame": args.frame,
        "working_dimensions": [args.width, args.height],
        "diagnostic_image_directory": str(args.image_dir),
        "seconds": time.perf_counter() - started,
        "v64_lattice_sha256": sha256(
            Path(__file__).resolve().parents[1]
            / "cache/print_2383_monitor_output_lut_193_v64.npy"
        ),
        "v66_lattice_sha256": sha256(
            Path(__file__).resolve().parents[1]
            / "cache/print_2383_monitor_output_lut_193_v66.npy"
        ),
        "selected_endpoint": "full_printing_density",
        "selection_rationale": (
            "Cineon data codes are defined in printing-density coordinates. "
            "A partial blend would preserve an aesthetic/device prior but "
            "would knowingly leave the data coordinate inconsistent."
        ),
        "printing_density_gate_17cube": density_gate,
        "t003_chart_diagnostic": chart_gate,
        "real_frame_vs_v64": {
            name: difference_metrics(image, baseline)
            for name, image in rendered.items()
        },
        "real_frame_luma": {
            name: luma_metrics(image) for name, image in rendered.items()
        },
        "cineon_code": {
            name: code_metrics(code) for name, code in codes.items()
        },
        "neutral_anchors": anchors,
        "coordinate_interpretation": {
            "v64_current": (
                "Broad period-telecine density blended 82 percent toward "
                "independent Status-M record density, with a four-point "
                "shoulder release."
            ),
            "printing_density": (
                "D-min-subtracted integral density seen by the active 3200 K "
                "printer and vector-traced 2383 record sensitivities, then "
                "normalized to Cineon 445 at neutral 18 percent."
            ),
            "evidence_boundary": (
                "Kodak identifies printing density as the calibration target "
                "for a data scan, but the exact Spirit optical filters, lamp, "
                "CCD response and production printer spectrum remain unknown."
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
