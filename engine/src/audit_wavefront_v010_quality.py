#!/usr/bin/env python3
"""Audit Wavefront candidates' spatial NPS and temporal negative statistics."""

from __future__ import annotations

import argparse
import gc
import json
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

from engine.emulsion5279 import legacy
from engine.emulsion5279.contracts import EngineConfig, EngineMode
from engine.emulsion5279.pipeline import Emulsion5279Engine


ANCHORS = {
    "centre": (0.50, 0.50),
    "upper_left": (0.16, 0.19),
    "upper_right": (0.84, 0.19),
    "lower_left": (0.16, 0.81),
    "lower_right": (0.84, 0.81),
}
NPS_EDGES = np.asarray(
    [0.0, 0.03125, 0.0625, 0.125, 0.25, 0.5, 0.71],
    dtype=np.float64,
)
QUALITY_GATES = {
    "maximum_absolute_spatial_rms_ratio_minus_one": 0.005,
    "maximum_absolute_temporal_rms_ratio_minus_one": 0.005,
    "maximum_absolute_normalized_nps_band_delta": 0.002,
    "maximum_absolute_temporal_lag1_correlation_delta": 0.005,
    "maximum_absolute_tail_ratio_minus_one": 0.01,
    "maximum_crop_density_delta": 2.0e-5,
}


def decode_frame(
    source: Path,
    decoder: Path,
    frame: int,
    cache_directory: Path,
) -> np.ndarray:
    width, height, _ = legacy.model.probe_video(source)
    cache = cache_directory / f"frame_{frame:06d}.npy"
    if cache.exists():
        raw = np.load(cache, mmap_mode="r")
        if raw.shape != (height, width, 3) or raw.dtype != np.float32:
            raise ValueError(f"invalid cached frame: {cache}")
        return np.asarray(raw)
    payload = subprocess.check_output(
        [str(decoder), str(source), str(frame), "1"],
        stderr=subprocess.DEVNULL,
    )
    raw = np.frombuffer(payload, dtype="<f4")
    if raw.size != width * height * 3:
        raise RuntimeError(f"decoded {raw.size} floats for frame {frame}")
    raw = raw.reshape(height, width, 3)
    cache_directory.mkdir(parents=True, exist_ok=True)
    np.save(cache, raw)
    return raw


def crop_coordinates(
    width: int, height: int, size: int
) -> dict[str, tuple[int, int]]:
    result = {}
    for name, (fraction_x, fraction_y) in ANCHORS.items():
        x = int(round(fraction_x * width - size / 2))
        y = int(round(fraction_y * height - size / 2))
        result[name] = (
            min(max(x, 0), width - size),
            min(max(y, 0), height - size),
        )
    return result


def render_negative_crops(
    engine: Emulsion5279Engine,
    source: Path,
    decoder: Path,
    cache_directory: Path,
    frame_indices: list[int],
    size: int,
    label: str,
) -> tuple[dict[str, np.ndarray], list[float]]:
    width, height, _ = legacy.model.probe_video(source)
    coordinates = crop_coordinates(width, height, size)
    rows: dict[str, list[np.ndarray]] = {name: [] for name in coordinates}
    timings = []
    for frame in frame_indices:
        raw = decode_frame(source, decoder, frame, cache_directory)
        started = time.perf_counter()
        negative = engine.form_negative(raw, frame)
        timings.append(time.perf_counter() - started)
        for name, (x, y) in coordinates.items():
            formed = negative.formed_record_density[y : y + size, x : x + size]
            mean = negative.mean_record_density[y : y + size, x : x + size]
            rows[name].append((formed - mean).astype(np.float32))
        print(
            f"{label} frame {frame}: {timings[-1]:.3f} s",
            flush=True,
        )
        del negative, raw
        gc.collect()
    return (
        {name: np.stack(values) for name, values in rows.items()},
        timings,
    )


def correlation(first: np.ndarray, second: np.ndarray) -> float:
    a = first.astype(np.float64, copy=False)
    b = second.astype(np.float64, copy=False)
    a = a - a.mean()
    b = b - b.mean()
    denominator = max(float(a.std() * b.std()), 1.0e-30)
    return float(np.mean(a * b) / denominator)


def normalized_nps(sequence: np.ndarray) -> list[list[float]]:
    _, height, width, records = sequence.shape
    window = np.outer(np.hanning(height), np.hanning(width)).astype(np.float32)
    fy = np.fft.fftfreq(height)[:, None]
    fx = np.fft.rfftfreq(width)[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    result = []
    for record in range(records):
        power = np.zeros((height, width // 2 + 1), dtype=np.float64)
        for frame in sequence[..., record]:
            centered = frame - float(frame.mean())
            transformed = np.fft.rfft2(centered * window)
            power += np.abs(transformed) ** 2
        bands = [
            float(power[(radius >= low) & (radius < high)].sum())
            for low, high in zip(NPS_EDGES[:-1], NPS_EDGES[1:])
        ]
        total = max(sum(bands), 1.0e-30)
        result.append([value / total for value in bands])
    return result


def sequence_metrics(sequence: np.ndarray) -> dict[str, object]:
    centered = sequence - sequence.mean(axis=(1, 2), keepdims=True)
    temporal = np.diff(centered, axis=0)
    spatial_rms = np.sqrt(np.mean(centered * centered, axis=(0, 1, 2)))
    temporal_rms = np.sqrt(np.mean(temporal * temporal, axis=(0, 1, 2)))
    absolute = np.abs(centered)
    lag1 = [
        correlation(centered[:-1, ..., record], centered[1:, ..., record])
        for record in range(3)
    ]
    return {
        "spatial_rms_records": spatial_rms.tolist(),
        "temporal_difference_rms_records": temporal_rms.tolist(),
        "absolute_density_p95_p99_p999_records": [
            np.percentile(absolute[..., record], [95, 99, 99.9]).tolist()
            for record in range(3)
        ],
        "temporal_lag1_correlation_records": lag1,
        "spatial_x_lag1_correlation_records": [
            correlation(
                centered[..., record][:, :, :-1],
                centered[..., record][:, :, 1:],
            )
            for record in range(3)
        ],
        "spatial_y_lag1_correlation_records": [
            correlation(
                centered[..., record][:, :-1, :],
                centered[..., record][:, 1:, :],
            )
            for record in range(3)
        ],
        "normalized_nps_bands_records": normalized_nps(centered),
    }


def compare_metrics(reference: dict, candidate: dict) -> dict[str, object]:
    spatial_ratio = np.asarray(candidate["spatial_rms_records"]) / np.maximum(
        np.asarray(reference["spatial_rms_records"]), 1.0e-30
    )
    temporal_ratio = np.asarray(
        candidate["temporal_difference_rms_records"]
    ) / np.maximum(
        np.asarray(reference["temporal_difference_rms_records"]), 1.0e-30
    )
    tails_ratio = np.asarray(
        candidate["absolute_density_p95_p99_p999_records"]
    ) / np.maximum(
        np.asarray(reference["absolute_density_p95_p99_p999_records"]),
        1.0e-30,
    )
    nps_delta = np.asarray(
        candidate["normalized_nps_bands_records"]
    ) - np.asarray(reference["normalized_nps_bands_records"])
    temporal_correlation_delta = np.asarray(
        candidate["temporal_lag1_correlation_records"]
    ) - np.asarray(reference["temporal_lag1_correlation_records"])
    return {
        "spatial_rms_ratio_records": spatial_ratio.tolist(),
        "temporal_difference_rms_ratio_records": temporal_ratio.tolist(),
        "absolute_density_tail_ratio_records": tails_ratio.tolist(),
        "normalized_nps_band_delta_records": nps_delta.tolist(),
        "temporal_lag1_correlation_delta_records": (
            temporal_correlation_delta.tolist()
        ),
        "maximum_absolute_spatial_rms_ratio_minus_one": float(
            np.max(np.abs(spatial_ratio - 1.0))
        ),
        "maximum_absolute_temporal_rms_ratio_minus_one": float(
            np.max(np.abs(temporal_ratio - 1.0))
        ),
        "maximum_absolute_normalized_nps_band_delta": float(
            np.max(np.abs(nps_delta))
        ),
        "maximum_absolute_temporal_lag1_correlation_delta": float(
            np.max(np.abs(temporal_correlation_delta))
        ),
        "maximum_absolute_tail_ratio_minus_one": float(
            np.max(np.abs(tails_ratio - 1.0))
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--cache-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--crop-size", type=int, default=512)
    parser.add_argument(
        "--candidate",
        choices=("v010", "v020"),
        default="v010",
    )
    args = parser.parse_args()
    if args.frames < 2:
        raise ValueError("temporal audit requires at least two frames")

    config = EngineConfig(profile="v43h", mode=EngineMode.PRODUCTION_METAL)
    engine = Emulsion5279Engine(config)
    engine.configure()
    import v35_accel
    import wavefront_tile_lab_v002
    import wavefront_tile_lab_v010
    import wavefront_tile_lab_v020

    frame_indices = list(range(args.start_frame, args.start_frame + args.frames))
    v35_accel.apply_metal_binomial(
        legacy.model,
        mode="bernoulli",
        asynchronous=True,
        domain_salt=config.grain_domain_salt,
    )
    if args.candidate == "v020":
        wavefront_tile_lab_v010.install(
            legacy.model, marginal_tile_pixels=250_000
        )
        reference_label = "v0.1.0"
    else:
        wavefront_tile_lab_v002.install(
            legacy.model, marginal_tile_pixels=250_000
        )
        reference_label = "v0.0.2"
    reference, reference_timings = render_negative_crops(
        engine,
        args.source,
        args.decoder,
        args.cache_directory,
        frame_indices,
        args.crop_size,
        reference_label,
    )
    if args.candidate == "v020":
        wavefront_tile_lab_v010.uninstall(legacy.model)
    else:
        wavefront_tile_lab_v002.uninstall(legacy.model)

    v35_accel.apply_metal_binomial(
        legacy.model,
        mode="bernoulli",
        asynchronous=True,
        domain_salt=config.grain_domain_salt,
    )
    if args.candidate == "v020":
        wavefront_tile_lab_v020.install(
            legacy.model, marginal_tile_pixels=250_000
        )
        candidate_label = "v0.2.0"
    else:
        wavefront_tile_lab_v010.install(
            legacy.model, marginal_tile_pixels=250_000
        )
        candidate_label = "v0.1.0"
    candidate, candidate_timings = render_negative_crops(
        engine,
        args.source,
        args.decoder,
        args.cache_directory,
        frame_indices,
        args.crop_size,
        candidate_label,
    )

    crop_results = {}
    maximum_crop_delta = 0.0
    summaries = []
    for name in ANCHORS:
        reference_metrics = sequence_metrics(reference[name])
        candidate_metrics = sequence_metrics(candidate[name])
        comparison = compare_metrics(reference_metrics, candidate_metrics)
        delta = np.abs(candidate[name] - reference[name])
        direct = {
            "maximum_absolute_density_delta": float(delta.max()),
            "root_mean_square_density_delta": float(
                np.sqrt(np.mean(delta * delta))
            ),
            "changed_fraction": float(np.mean(delta != 0.0)),
        }
        maximum_crop_delta = max(
            maximum_crop_delta, direct["maximum_absolute_density_delta"]
        )
        crop_results[name] = {
            "reference": reference_metrics,
            "candidate": candidate_metrics,
            "candidate_vs_reference": comparison,
            "direct_float32_difference": direct,
        }
        summaries.append(comparison)

    summary = {
        key: max(float(row[key]) for row in summaries)
        for key in QUALITY_GATES
        if key != "maximum_crop_density_delta"
    }
    summary["maximum_crop_density_delta"] = maximum_crop_delta
    gate_results = {
        key: summary[key] <= limit for key, limit in QUALITY_GATES.items()
    }
    report = {
        "experiment": f"Wavefront Tile Lab {candidate_label} quality audit",
        "source": str(args.source),
        "frames": frame_indices,
        "crop_size": args.crop_size,
        "anchors": ANCHORS,
        "nps_band_edges_cycles_per_pixel": NPS_EDGES.tolist(),
        "timing_seconds": {
            "reference_label": reference_label,
            "candidate_label": candidate_label,
            "reference": reference_timings,
            "candidate": candidate_timings,
            "reference_median": float(np.median(reference_timings)),
            "candidate_median": float(np.median(candidate_timings)),
        },
        "quality_gates": QUALITY_GATES,
        "summary": summary,
        "gate_results": gate_results,
        "all_quality_gates_pass": all(gate_results.values()),
        "crops": crop_results,
        "interpretation_boundary": (
            "Three real-scene frames are a regression screen, not a published "
            "5279 NPS measurement or a final temporal release qualification."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": summary, "gates": gate_results}, indent=2))
    engine.close()


if __name__ == "__main__":
    main()
