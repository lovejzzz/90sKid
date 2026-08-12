#!/usr/bin/env python3
"""Audit ownership and uncertainty in the V64 projection observer.

This is deliberately diagnostic. It does not select a new display rendering.
Each ablation starts from V64 and changes one observer assumption at a time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

import emulsion_experiment as e
import v64_profile
from apply_v31_normal_process_adapter import adapt_frame_linear
from audit_v63_neutral_trajectory import difference_metrics
from audit_v64_2383_density_shaper import decode_reduced, luma_metrics


V64_CALLIER_GAIN_RGB = np.array([0.012, 0.010, 0.014], dtype=np.float32)
V64_TYPICAL_FLARE = 0.01


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def formed_mean_density(raw: np.ndarray) -> np.ndarray:
    v64_profile.apply(e)
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=0.45,
        raw_colour="panasonic_official",
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    return e.develop_5279_record_density(e.film_records_from_rgb(film))


def observe(
    records: np.ndarray,
    *,
    authority: str,
    callier_gain: np.ndarray | None = None,
    flare: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    v64_profile.apply(e)
    e.PRINT_MONITOR_COLOUR_AUTHORITY = authority
    # Profile application intentionally inherits these historical observer
    # constants. Restore them explicitly so a preceding ablation cannot leak
    # into the next one in the same interpreter.
    e.PRINT_2383_CALLIER_GAIN_RGB = V64_CALLIER_GAIN_RGB.copy()
    e.TYPICAL_CINEMA_PROJECTION_FLARE = V64_TYPICAL_FLARE
    if callier_gain is not None:
        e.PRINT_2383_CALLIER_GAIN_RGB = np.asarray(
            callier_gain, dtype=np.float32
        )
    if flare is not None:
        e.TYPICAL_CINEMA_PROJECTION_FLARE = float(flare)
    e.refresh_5279_spectral_observer_caches()
    projection = e.render_2383_monitor_projection_from_record_density(records)
    scan = e.finish_cineon_scan_for_bluray(
        e.render_cineon_scan_master_from_record_density(records)
    )
    return projection, scan


def observer_chroma_summary(image: np.ndarray) -> dict[str, float]:
    lab = e.linear_rec709_to_oklab(np.maximum(image, 0.0))
    chroma = np.linalg.norm(lab[..., 1:3], axis=-1)
    return {
        "median": float(np.median(chroma)),
        "p95": float(np.percentile(chroma, 95)),
        "p99": float(np.percentile(chroma, 99)),
        "maximum": float(np.max(chroma)),
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
    args = parser.parse_args()

    started = time.perf_counter()
    raw = decode_reduced(
        args.source, args.decoder, args.frame, args.width, args.height
    )
    records = formed_mean_density(raw)

    internal_scan, scan = observe(
        records, authority="scan_referenced_v31"
    )
    delivered_scan = adapt_frame_linear(
        internal_scan, scan, opponent_high_frequency_retention=0.0
    )
    physical, physical_scan = observe(
        records, authority="physical_spectral_v56"
    )
    no_callier, _ = observe(
        records,
        authority="physical_spectral_v56",
        callier_gain=np.zeros(3, dtype=np.float32),
    )
    internal_scan_no_callier, _ = observe(
        records,
        authority="scan_referenced_v31",
        callier_gain=np.zeros(3, dtype=np.float32),
    )
    delivered_scan_no_callier = adapt_frame_linear(
        internal_scan_no_callier,
        scan,
        opponent_high_frequency_retention=0.0,
    )
    no_flare, _ = observe(
        records,
        authority="physical_spectral_v56",
        flare=0.0,
    )

    # The physical experiment still uses the scan only for its near-neutral
    # highlight guard. Compare its returned scan to the independent baseline
    # to prove the observer variants share one negative/scan branch.
    scan_gate = difference_metrics(scan, physical_scan)

    result = {
        "audit": "V65 projection-observer ownership and uncertainty audit",
        "status": "diagnostic_only_no_release_selection",
        "source": str(args.source),
        "frame": args.frame,
        "working_dimensions": [args.width, args.height],
        "seconds": time.perf_counter() - started,
        "v64_lattice_sha256": sha256(
            Path(__file__).resolve().parents[1]
            / "cache/print_2383_monitor_output_lut_193_v64.npy"
        ),
        "observer_ownership": {
            "physical_vs_delivered_scan_referenced": difference_metrics(
                physical, delivered_scan
            ),
            "internal_vs_final_scan_reference": difference_metrics(
                internal_scan, delivered_scan
            ),
            "scan_shared_across_variants": scan_gate,
        },
        "single_variable_ablations": {
            "zero_callier_vs_v64_physical": difference_metrics(
                no_callier, physical
            ),
            "zero_callier_vs_v64_delivered": difference_metrics(
                delivered_scan_no_callier, delivered_scan
            ),
            "zero_flare_vs_v64_physical": difference_metrics(
                no_flare, physical
            ),
        },
        "luma": {
            "scan": luma_metrics(scan),
            "delivered_scan_referenced_projection": luma_metrics(
                delivered_scan
            ),
            "physical_spectral_projection": luma_metrics(physical),
            "physical_zero_callier": luma_metrics(no_callier),
            "delivered_zero_callier": luma_metrics(
                delivered_scan_no_callier
            ),
            "physical_zero_flare": luma_metrics(no_flare),
        },
        "oklab_chroma": {
            "scan": observer_chroma_summary(scan),
            "delivered_scan_referenced_projection": observer_chroma_summary(
                delivered_scan
            ),
            "physical_spectral_projection": observer_chroma_summary(physical),
            "physical_zero_callier": observer_chroma_summary(no_callier),
            "delivered_zero_callier": observer_chroma_summary(
                delivered_scan_no_callier
            ),
            "physical_zero_flare": observer_chroma_summary(no_flare),
        },
        "interpretation": {
            "delivery": (
                "V40+ final publication retains projection lightness/luma but "
                "sets low-frequency opponent colour from the period-scan "
                "observer; projection and scan similarity is therefore a "
                "declared safety boundary, not evidence that the optical "
                "observers are naturally equivalent."
            ),
            "callier": (
                "The nonzero Callier gain is a generic subtle-colour-print "
                "prior, not a measured 2383 Q(D, wavelength) function."
            ),
            "flare": (
                "The scalar one-percent veil is a viewing-condition prior, "
                "not a spatially measured projector/lens/port/screen flare "
                "kernel. It is currently unreachable in both active monitor "
                "colour-authority branches, so changing it cannot explain the "
                "delivered black or projection/scan difference."
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
