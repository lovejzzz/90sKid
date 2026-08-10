#!/usr/bin/env python3
"""Exactness and performance lab for bounded V43H Metal point sampling.

This experiment deliberately tiles only the finite-site Philox/Bernoulli
stage. Whole-frame optical filters, DIR chemistry and both observers remain on
the accepted V43H graph, so an arbitrary tile edge can never become a film
boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import subprocess
import time
from functools import wraps
from pathlib import Path

import numpy as np

from engine.emulsion5279 import legacy
from engine.emulsion5279.contracts import EngineConfig, EngineMode
from engine.emulsion5279.pipeline import Emulsion5279Engine


def decode_frame(
    source: Path, decoder: Path, frame: int, cache: Path
) -> np.ndarray:
    width, height, _ = legacy.model.probe_video(source)
    if cache.exists():
        raw = np.load(cache, mmap_mode="r")
        if raw.shape != (height, width, 3) or raw.dtype != np.float32:
            raise ValueError(f"invalid cached frame: {cache}")
        return np.asarray(raw)
    process = subprocess.run(
        [str(decoder), str(source), str(frame), "1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    raw = np.frombuffer(process.stdout, dtype="<f4")
    expected = width * height * 3
    if raw.size != expected:
        raise RuntimeError(f"decoded {raw.size} floats; expected {expected}")
    raw = raw.reshape(height, width, 3)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.save(cache, raw)
    return raw


def sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def u16_signal(array: np.ndarray) -> np.ndarray:
    return np.rint(np.clip(array, 0.0, 1.0) * 65535.0).astype("<u2")


def compare_reference(
    name: str, candidate: np.ndarray, reference: Path
) -> dict[str, object]:
    path = reference / f"{name}.npy"
    baseline = np.load(path, mmap_mode="r")
    if baseline.shape != candidate.shape or baseline.dtype != candidate.dtype:
        raise ValueError(f"reference contract mismatch: {path}")
    candidate_hash = sha256(candidate)
    baseline_hash = sha256(baseline)
    total = int(candidate.size)
    signed_sum = 0.0
    absolute_sum = 0.0
    squared_sum = 0.0
    quantized_12bit_changed = 0
    quantized_12bit_maximum = 0
    if candidate_hash == baseline_hash:
        maximum = 0.0
        changed = 0
    else:
        maximum = 0.0
        changed = 0
        for y0 in range(0, candidate.shape[0], 64):
            y1 = min(y0 + 64, candidate.shape[0])
            signed_delta = (
                candidate[y0:y1].astype(np.float64)
                - baseline[y0:y1].astype(np.float64)
            )
            delta = np.abs(signed_delta)
            maximum = max(maximum, float(delta.max()))
            changed += int(np.count_nonzero(delta))
            signed_sum += float(signed_delta.sum())
            absolute_sum += float(delta.sum())
            squared_sum += float(np.square(signed_delta).sum())
            if candidate.dtype == np.dtype("<u2"):
                candidate_12bit = np.rint(
                    candidate[y0:y1].astype(np.float64) / 65535.0 * 4095.0
                ).astype(np.int32)
                baseline_12bit = np.rint(
                    baseline[y0:y1].astype(np.float64) / 65535.0 * 4095.0
                ).astype(np.int32)
                delta_12bit = np.abs(candidate_12bit - baseline_12bit)
                quantized_12bit_changed += int(np.count_nonzero(delta_12bit))
                quantized_12bit_maximum = max(
                    quantized_12bit_maximum,
                    int(delta_12bit.max()),
                )
    result = {
        "identical": candidate_hash == baseline_hash,
        "candidate_sha256": candidate_hash,
        "reference_sha256": baseline_hash,
        "maximum_absolute_delta": maximum,
        "changed_values": changed,
        "changed_fraction": changed / total,
        "mean_signed_delta": signed_sum / total,
        "mean_absolute_delta": absolute_sum / total,
        "root_mean_square_delta": math.sqrt(squared_sum / total),
    }
    if candidate.dtype == np.dtype("<u2"):
        result.update(
            {
                "quantized_12bit_changed_values": quantized_12bit_changed,
                "quantized_12bit_changed_fraction": (
                    quantized_12bit_changed / total
                ),
                "quantized_12bit_maximum_absolute_delta": (
                    quantized_12bit_maximum
                ),
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--save-reference", action="store_true")
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--workset-pixels", type=int, default=0)
    parser.add_argument("--in-flight", type=int, default=2)
    parser.add_argument("--negative-only", action="store_true")
    parser.add_argument("--marginal-workset-pixels", type=int, default=0)
    parser.add_argument("--v002", action="store_true")
    parser.add_argument("--v010", action="store_true")
    parser.add_argument("--v020", action="store_true")
    args = parser.parse_args()
    if args.workset_pixels < 0:
        raise ValueError("workset pixels cannot be negative")

    args.output.mkdir(parents=True, exist_ok=True)
    config = EngineConfig(
        profile="v43h",
        mode=EngineMode.PRODUCTION_METAL,
        observer_branch_workers=2,
    )
    # v27_accel captures these dictionaries while the engine is configured.
    # Install them first so operator-level timings are not silently omitted.
    legacy.model._V27_MEAN_PROFILE = {}
    legacy.model._V27_STOCHASTIC_PROFILE = {}
    engine = Emulsion5279Engine(config)
    engine.configure()

    import metal_binomial_bridge
    import v35_accel

    if args.workset_pixels:
        v35_accel.apply_metal_binomial(
            legacy.model,
            mode="bernoulli",
            asynchronous=True,
            domain_salt=config.grain_domain_salt,
            tile_workset_pixels=args.workset_pixels,
            tile_in_flight=args.in_flight,
        )
        v35_accel.warm_metal_binomial("bernoulli")
    wavefront_v001 = None
    wavefront_v002 = None
    wavefront_v010 = None
    wavefront_v020 = None
    if args.v020:
        import wavefront_tile_lab_v020 as wavefront_v020

        wavefront_v020.install(
            legacy.model,
            marginal_tile_pixels=args.marginal_workset_pixels or 250_000,
        )
    elif args.v010:
        import wavefront_tile_lab_v010 as wavefront_v010

        wavefront_v010.install(
            legacy.model,
            marginal_tile_pixels=args.marginal_workset_pixels or 250_000,
        )
    elif args.v002:
        import wavefront_tile_lab_v002 as wavefront_v002

        wavefront_v002.install(
            legacy.model,
            marginal_tile_pixels=args.marginal_workset_pixels or 250_000,
        )
    elif args.marginal_workset_pixels:
        import wavefront_tile_lab_v001 as wavefront_v001

        wavefront_v001.install(
            legacy.model, tile_pixels=args.marginal_workset_pixels
        )
    for key in metal_binomial_bridge.STATS:
        metal_binomial_bridge.STATS[key] = 0
    negative_stage_profile: dict[str, dict[str, float | int]] = {}
    for function_name in (
        "scene_to_5279_film_rgb",
        "film_records_from_rgb",
        "develop_5279_record_density",
        "form_5279_multilayer_record_density",
    ):
        original = getattr(legacy.model, function_name)

        @wraps(original)
        def profiled(*positional, _name=function_name, _original=original, **keywords):
            function_started = time.perf_counter()
            result = _original(*positional, **keywords)
            entry = negative_stage_profile.setdefault(
                _name, {"calls": 0, "seconds": 0.0}
            )
            entry["calls"] = int(entry["calls"]) + 1
            entry["seconds"] = (
                float(entry["seconds"])
                + time.perf_counter()
                - function_started
            )
            return result

        setattr(legacy.model, function_name, profiled)

    raw = decode_frame(args.source, args.decoder, args.frame, args.cache)
    started = time.perf_counter()
    mark = started
    negative = engine.form_negative(raw, args.frame)
    negative_seconds = time.perf_counter() - mark
    if args.negative_only:
        encoded = None
        observer_seconds = 0.0
        encoding_seconds = 0.0
    else:
        mark = time.perf_counter()
        observers = engine.observe(negative, args.frame)
        observer_seconds = time.perf_counter() - mark
        mark = time.perf_counter()
        encoded = engine.encode_reference(observers)
        encoding_seconds = time.perf_counter() - mark
    wall_seconds = time.perf_counter() - started

    arrays = {"formed_density_f32": negative.formed_record_density}
    if encoded is not None:
        arrays.update(
            {
                "projection_u16": u16_signal(encoded.projection),
                "scan_u16": u16_signal(encoded.scan),
            }
        )
    comparisons = (
        {
            name: compare_reference(name, array, args.reference)
            for name, array in arrays.items()
        }
        if args.reference
        else {}
    )
    if args.save_reference:
        for name, array in arrays.items():
            np.save(args.output / f"{name}.npy", array)

    height, width = negative.formed_record_density.shape[:2]
    plane_bytes = height * width * np.dtype(np.float32).itemsize
    if args.workset_pixels:
        row_bytes = width * np.dtype(np.float32).itemsize
        alignment_rows = 16_384 // math.gcd(16_384, row_bytes)
        requested_rows = max(1, args.workset_pixels // width)
        tile_rows = (
            max(
                alignment_rows,
                requested_rows // alignment_rows * alignment_rows,
            )
            if requested_rows >= alignment_rows
            else requested_rows
        )
        actual_tile_pixels = min(height, tile_rows) * width
    else:
        actual_tile_pixels = height * width
    sampler_transient = (
        plane_bytes * 2
        if not args.workset_pixels
        else plane_bytes
    )
    wavefront_snapshot = None
    if wavefront_v010 is not None:
        wavefront_snapshot = wavefront_v010.snapshot()
    elif wavefront_v020 is not None:
        wavefront_snapshot = wavefront_v020.snapshot()
    elif wavefront_v002 is not None:
        wavefront_snapshot = wavefront_v002.snapshot()
    elif wavefront_v001 is not None:
        wavefront_snapshot = wavefront_v001.snapshot()
    lab_version = (
        "0.2.0"
        if wavefront_v020 is not None
        else "0.1.0"
        if wavefront_v010 is not None
        else "0.0.2"
        if wavefront_v002 is not None
        else "0.0.1" if wavefront_v001 is not None else None
    )
    report = {
        "experiment": (
            f"Wavefront Tile Lab v{lab_version}"
            if lab_version is not None
            else "V43H Wavefront Tile Lab"
        ),
        "scope": (
            "v0.1.0 resident Metal emulsion plus algebraically collapsed V41 "
            "input residual and separable deterministic mean-DIR batch; film "
            "equations and observer equations remain unchanged"
            if wavefront_v020 is not None
            else
            "one-command Metal island for five-size-class Philox sampling, "
            "optical integration, phase and population accumulation; film "
            "equations remain unchanged"
            if wavefront_v010 is not None
            else
            "exact in-place optical-buffer and class-accumulation contraction, "
            "including the v0.0.1 activation-to-DIR-marginal contraction"
            if wavefront_v002 is not None
            else "exact tiled activation-to-DIR-marginal lifetime contraction; "
            "finite-site sampling, optical filtering, DIR equations, "
            "projection and scan remain unchanged"
            if wavefront_v001 is not None
            else "finite-site Philox/Bernoulli only; optical filtering, DIR, "
            "projection and scan remain whole-frame"
        ),
        "source": str(args.source),
        "absolute_frame": args.frame,
        "negative_only": args.negative_only,
        "shape": [height, width],
        "candidate": {
            "workset_pixels_requested": args.workset_pixels or None,
            "workset_pixels_actual_max": actual_tile_pixels,
            "in_flight": args.in_flight if args.workset_pixels else 1,
            "full_width_row_tiles": bool(args.workset_pixels),
            "marginal_workset_pixels": (
                (args.marginal_workset_pixels or 250_000)
                if args.v002 or args.v010 or args.v020
                else args.marginal_workset_pixels or None
            ),
            "lab_version": lab_version,
        },
        "timing_seconds": {
            "negative_formation": negative_seconds,
            "dual_observer": observer_seconds,
            "delivery_encoding": encoding_seconds,
            "total": wall_seconds,
        },
        "memory": {
            "peak_rss_gib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            / 1024**3,
            "scalar_plane_mib": plane_bytes / 1024**2,
            "estimated_sampler_transient_mib": sampler_transient / 1024**2,
            "activation_tensor_mib": plane_bytes * 9 / 1024**2,
            "v001_marginal_scratch_mib": (
                None
                if wavefront_snapshot is None
                else float(
                    (
                        wavefront_snapshot["v010"]["v002"]["v001"]
                        if wavefront_v020 is not None
                        else wavefront_snapshot["v002"]["v001"]
                        if wavefront_v010 is not None
                        else wavefront_snapshot["v001"]
                        if wavefront_v002 is not None
                        else wavefront_snapshot
                    )["maximum_scratch_bytes"]
                )
                / 1024**2
            ),
        },
        "hashes": {name: sha256(array) for name, array in arrays.items()},
        "reference_comparison": comparisons,
        "all_reference_arrays_identical": bool(comparisons)
        and all(row["identical"] for row in comparisons.values()),
        "metal_sampler_stats": dict(metal_binomial_bridge.STATS),
        "wavefront_v001_stats": (
            wavefront_snapshot["v010"]["v002"]["v001"]
            if wavefront_v020 is not None
            else wavefront_snapshot["v002"]["v001"]
            if wavefront_v010 is not None
            else wavefront_snapshot["v001"]
            if wavefront_v002 is not None
            else wavefront_snapshot
        ),
        "wavefront_v002_stats": (
            wavefront_snapshot["v010"]["v002"]
            if wavefront_v020 is not None
            else wavefront_snapshot["v002"]
            if wavefront_v010 is not None
            else wavefront_snapshot
            if wavefront_v002 is not None
            else None
        ),
        "wavefront_v010_stats": (
            wavefront_snapshot["v010"]
            if wavefront_v020 is not None
            else wavefront_snapshot if wavefront_v010 is not None else None
        ),
        "wavefront_v020_stats": (
            wavefront_snapshot if wavefront_v020 is not None else None
        ),
        "sampler_identity_audit": v35_accel.sampler_audit_snapshot(),
        "mean_operator_profile": legacy.model._V27_MEAN_PROFILE,
        "stochastic_operator_profile": legacy.model._V27_STOCHASTIC_PROFILE,
        "negative_stage_profile": negative_stage_profile,
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2), flush=True)
    engine.close()


if __name__ == "__main__":
    main()
