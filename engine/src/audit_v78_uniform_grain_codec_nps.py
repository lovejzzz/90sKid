#!/usr/bin/env python3
"""Compare delivery codecs against uniform formed-minus-mean grain NPS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np

import emulsion_experiment as e
from audit_v75_scale_integrated_delivery import exact_integer_area
from audit_v76_review_codec_ownership import commands, output_path
from audit_v77_frequency_and_projection_grain_observer import (
    FRAME_WIDTH_MM,
    describe_rgb_residual,
    render_observers,
    uniform_negative,
)
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.pipeline import Emulsion5279Engine, FormedNegative


CANDIDATES = (
    "prores_ks_xq",
    "prores_ks_xq_8192",
    "prores_videotoolbox_xq",
    "ffv1_lossless",
)
BRANCHES = ("archive_pointwise_projection", "legacy_managed_scan")


def decode_linear(path: Path, width: int, height: int) -> np.ndarray:
    payload = subprocess.check_output(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-frames:v",
            "1",
            "-vf",
            (
                "setparams=color_primaries=bt709:color_trc=bt709:"
                "colorspace=bt709"
            ),
            "-pix_fmt",
            "rgb48le",
            "-f",
            "rawvideo",
            "-",
        ]
    )
    expected = width * height * 3 * 2
    if len(payload) != expected:
        raise RuntimeError(f"short codec decode {len(payload)}/{expected}: {path}")
    code = (
        np.frombuffer(payload, "<u2")
        .reshape(height, width, 3)
        .astype(np.float32)
        / 65535.0
    )
    return e.srgb_decode(code)


def encode_one(
    image: np.ndarray,
    root: Path,
    candidate: str,
    fps: str,
) -> tuple[np.ndarray, int]:
    height, width = image.shape[:2]
    root.mkdir(parents=True, exist_ok=True)
    command = commands(root, width, height, fps)[candidate]
    path = output_path(command)
    payload = (
        np.rint(np.clip(e.srgb_encode(image), 0.0, 1.0) * 65535.0)
        .astype("<u2")
        .tobytes()
    )
    completed = subprocess.run(
        command,
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"{candidate} failed: "
            + completed.stderr.decode("utf-8", "replace")
        )
    if path.suffix == ".mov":
        e.finalize_prores_srgb_metadata(path)
    size = path.stat().st_size
    decoded = decode_linear(path, width, height)
    path.unlink(missing_ok=True)
    return decoded, size


def spectral_error(
    reference: dict[str, object], candidate: dict[str, object]
) -> dict[str, object]:
    result: dict[str, object] = {}
    for component in ("luma", "opponent"):
        ref = reference[component]
        got = candidate[component]
        ref_rms = float(ref["total_rms"])
        got_rms = float(got["total_rms"])
        ref_bands = np.asarray(ref["band_rms_equivalent"], dtype=np.float64)
        got_bands = np.asarray(got["band_rms_equivalent"], dtype=np.float64)
        nonzero_reference = ref_rms > 1e-8
        populated = ref_bands > max(ref_rms * 0.01, 1e-8)
        normalized_rmse: float | None = (
            float(
                np.sqrt(np.mean((got_bands - ref_bands) ** 2))
                / ref_rms
            )
            if nonzero_reference
            else None
        )
        if np.any(populated):
            log_error_db = 20.0 * np.log10(
                np.maximum(got_bands[populated], 1e-30)
                / ref_bands[populated]
            )
            mean_absolute_log_error_db: float | None = float(
                np.mean(np.abs(log_error_db))
            )
            maximum_absolute_log_error_db: float | None = float(
                np.max(np.abs(log_error_db))
            )
        else:
            mean_absolute_log_error_db = None
            maximum_absolute_log_error_db = None
        result[component] = {
            "reference_total_rms": ref_rms,
            "candidate_total_rms": got_rms,
            "total_rms_retention": (
                got_rms / ref_rms if nonzero_reference else None
            ),
            "absolute_added_rms_when_reference_near_zero": (
                got_rms if not nonzero_reference else None
            ),
            "band_rmse_over_reference_total_rms": normalized_rmse,
            "mean_absolute_populated_band_error_db": mean_absolute_log_error_db,
            "maximum_absolute_populated_band_error_db": (
                maximum_absolute_log_error_db
            ),
            "band_rms_candidate_minus_reference": (
                got_bands - ref_bands
            ).tolist(),
        }
    return result


def uniform_negative_sized(
    log_exposure: float, frame: int, height: int
) -> FormedNegative:
    if height == 192:
        return uniform_negative(log_exposure, frame)
    width = 5760
    records = np.full(
        (height, width, 3), 10.0 ** (log_exposure + 1.0), dtype=np.float32
    )
    log_field = np.full_like(records, log_exposure, dtype=np.float32)
    activations = e.subemulsion_activation_probabilities(log_field)
    mean = e.develop_5279_record_density_from_log_exposure(
        log_field, precomputed_activations=activations
    )
    formed = e.form_5279_multilayer_record_density(
        records,
        frame,
        1.0,
        1,
        precomputed_mean_density=mean,
        precomputed_log_exposure=log_field,
        precomputed_activations=activations,
    )
    return FormedNegative(mean, formed)


def integrated_branch_pair(
    observers: dict[str, np.ndarray], branch: str
) -> tuple[np.ndarray, np.ndarray]:
    if branch == "archive_pointwise_projection":
        formed = observers["projection"]
        mean = observers["mean_projection"]
    elif branch == "legacy_managed_scan":
        formed = observers["scan"]
        mean = observers["mean_scan"]
    else:
        raise ValueError(branch)
    return exact_integer_area(formed, 3), exact_integer_area(mean, 3)


def audit_condition(
    engine: Emulsion5279Engine,
    log_exposure: float,
    frame: int,
    fps: str,
    temporary: Path,
    height: int = 192,
) -> dict[str, object]:
    negative = uniform_negative_sized(log_exposure, frame, height)
    observers = render_observers(engine, negative, frame, "archive_pointwise")
    result: dict[str, object] = {
        "log_exposure": log_exposure,
        "source_dimensions": [5760, height],
        "review_dimensions": [1920, height // 3],
        "branches": {},
    }
    pixels_per_mm = 1920.0 / FRAME_WIDTH_MM
    for branch in BRANCHES:
        formed, mean = integrated_branch_pair(observers, branch)
        reference_residual = formed - mean
        reference_spectrum = describe_rgb_residual(
            reference_residual, pixels_per_mm
        )
        candidates: dict[str, object] = {}
        for candidate in CANDIDATES:
            formed_decoded, formed_bytes = encode_one(
                formed,
                temporary / f"{frame}-{branch}-{candidate}-formed",
                candidate,
                fps,
            )
            mean_decoded, mean_bytes = encode_one(
                mean,
                temporary / f"{frame}-{branch}-{candidate}-mean",
                candidate,
                fps,
            )
            candidate_spectrum = describe_rgb_residual(
                formed_decoded - mean_decoded, pixels_per_mm
            )
            candidates[candidate] = {
                "formed_plus_mean_bytes": formed_bytes + mean_bytes,
                "spectrum": candidate_spectrum,
                "error": spectral_error(reference_spectrum, candidate_spectrum),
            }
        result["branches"][branch] = {
            "reference": reference_spectrum,
            "candidates": candidates,
        }
    return result


def aggregate(rows: list[dict[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for candidate in CANDIDATES:
        band_errors: list[float] = []
        rms_errors: list[float] = []
        db_errors: list[float] = []
        bytes_values: list[int] = []
        nonzero_components = 0
        for row in rows:
            for branch in BRANCHES:
                item = row["branches"][branch]["candidates"][candidate]
                bytes_values.append(int(item["formed_plus_mean_bytes"]))
                for component in ("luma", "opponent"):
                    error = item["error"][component]
                    band_error = error["band_rmse_over_reference_total_rms"]
                    if band_error is not None:
                        band_errors.append(float(band_error))
                    retention = error["total_rms_retention"]
                    if retention is not None:
                        nonzero_components += 1
                        rms_errors.append(abs(float(retention) - 1.0))
                    db_error = error["mean_absolute_populated_band_error_db"]
                    if db_error is not None:
                        db_errors.append(float(db_error))
        result[candidate] = {
            "conditions": len(rows) * len(BRANCHES),
            "nonzero_luma_or_opponent_components": nonzero_components,
            "mean_band_rmse_over_reference_total_rms": float(
                np.mean(band_errors) if band_errors else 0.0
            ),
            "maximum_band_rmse_over_reference_total_rms": float(
                np.max(band_errors) if band_errors else 0.0
            ),
            "mean_absolute_total_rms_error_fraction": float(
                np.mean(rms_errors) if rms_errors else 0.0
            ),
            "mean_absolute_populated_band_error_db": float(
                np.mean(db_errors) if db_errors else 0.0
            ),
            "mean_formed_plus_mean_bytes": float(np.mean(bytes_values)),
        }
    return result


def summarize_v76_real_scene(path: Path) -> dict[str, object]:
    report = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, object] = {"source": str(path), "candidates": {}}
    for candidate in ("prores_ks_xq", "prores_ks_xq_8192", "prores_videotoolbox_xq"):
        rgb_mae: list[float] = []
        oklab_p95: list[float] = []
        structure_error: list[float] = []
        for branch in ("projection", "bluray_scan"):
            item = report["branches"][branch]["encodings"][candidate]["comparison"]
            rgb_mae.append(float(item["linear_light_difference"]["linear_rgb_mae"]))
            oklab_p95.append(float(item["linear_light_difference"]["oklab_delta_p95"]))
            structure_error.extend(
                (
                    abs(float(item["highpass_luma_retention"]) - 1.0),
                    abs(float(item["highpass_opponent_retention"]) - 1.0),
                )
            )
        result["candidates"][candidate] = {
            "mean_linear_rgb_mae": float(np.mean(rgb_mae)),
            "mean_oklab_p95": float(np.mean(oklab_p95)),
            "mean_absolute_highpass_retention_error": float(
                np.mean(structure_error)
            ),
        }
    return result


def measure(v76_path: Path) -> dict[str, object]:
    config = EngineConfig(
        profile="v72",
        exposure_stops=0.45,
        grain_scale=1.0,
        oversample=1,
        mode=EngineMode.PRODUCTION_METAL,
        opencv_threads=8,
        binomial_workers=8,
        numba_threads=8,
        array_workers=8,
        observer_branch_workers=1,
        research_baseline=True,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    try:
        with tempfile.TemporaryDirectory(prefix="v78-codec-nps-") as directory:
            root = Path(directory)
            rows = [
                audit_condition(
                    engine,
                    log_exposure,
                    7800 + index * 100,
                    "24000/1001",
                    root,
                )
                for index, log_exposure in enumerate((-3.0, -1.0, 0.0))
            ]
            full_frame = audit_condition(
                engine,
                -1.0,
                8190,
                "24000/1001",
                root,
                height=4320,
            )
    finally:
        engine.close()
    strip_summary = aggregate(rows)
    full_frame_summary = aggregate([full_frame])
    prores_ranking = sorted(
        (candidate for candidate in CANDIDATES if candidate != "ffv1_lossless"),
        key=lambda candidate: (
            full_frame_summary[candidate][
                "mean_band_rmse_over_reference_total_rms"
            ],
            full_frame_summary[candidate]["mean_absolute_total_rms_error_fraction"],
        ),
    )
    real_scene = summarize_v76_real_scene(v76_path)
    return {
        "audit": "V78 uniform grain codec NPS",
        "profile": "V72 · Evidence-minimal record formation",
        "image_change": "none; delivery candidate selection",
        "frequency_band_edges_lp_mm": [
            0.0, 4.0, 8.0, 16.0, 24.0, 32.0, 48.0, 64.0, 96.0, 128.0, 170.0
        ],
        "conditions": rows,
        "strip_aggregate": strip_summary,
        "full_frame_condition": full_frame,
        "full_frame_aggregate": full_frame_summary,
        "prores_ranking_by_full_frame_uniform_nps_error": prores_ranking,
        "real_scene_v76_reconciliation": real_scene,
        "combined_decision": (
            "Retain prores_ks XQ at 8192 bits/MB for normal QuickTime delivery. "
            "VideoToolbox ranks first on uniform NPS but has substantially "
            "larger T020 RGB/OKLab error and slight high-pass overshoot; its "
            "statistical retention is not pixel fidelity. Maximum-budget "
            "prores_ks improves both real-scene and uniform-NPS accuracy over "
            "default XQ without overshoot. FFV1 remains the exact lossless "
            "research control."
        ),
        "decision_rule": (
            "Prefer the QuickTime-compatible ProRes candidate with the lowest "
            "formed-minus-mean band error, provided it does not create a larger "
            "total-RMS error. FFV1 is the exact lossless control."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--v76",
        type=Path,
        default=Path("engine/research_runs/v76_review_codec_ownership_audit.json"),
    )
    args = parser.parse_args()
    report = measure(args.v76)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
