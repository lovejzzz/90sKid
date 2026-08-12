#!/usr/bin/env python3
"""Separate physical projection grain from inherited delivery management.

V40 changed two independent colour-frequency boundaries at once: it removed
the projection observer's unresolved high-frequency opponent remainder and it
also removed the projection opponent residual from V31's final scan-referenced
publication adapter.  Later releases retained both choices.  V79 holds one
formed V72 negative fixed and independently exposes those historical endpoints
without promoting any of them as a measured 5279/2383 property.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
from pathlib import Path

import numpy as np

import emulsion_experiment as e
from apply_v31_normal_process_adapter import adapt_frame_linear
from audit_v63_neutral_trajectory import difference_metrics
from audit_v75_scale_integrated_delivery import exact_integer_area
from audit_v77_frequency_and_projection_grain_observer import (
    FRAME_WIDTH_MM,
    LUMA,
    centred_crop,
    centred_crop_rect,
    describe_rgb_residual,
    measure_mean_relative_grain_tail,
    uniform_negative,
)
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import ProResRawDecoder
from emulsion5279.pipeline import Emulsion5279Engine, FormedNegative


POLICIES: dict[str, dict[str, float | str]] = {
    "current_v72_managed": {
        "local_hf_retention": 0.0,
        "local_opponent_strength": 0.66,
        "publication": "scan_referenced",
        "publication_hf_retention": 0.0,
    },
    "restore_v31_publication_only": {
        "local_hf_retention": 0.0,
        "local_opponent_strength": 0.66,
        "publication": "scan_referenced",
        "publication_hf_retention": 1.0,
    },
    "historical_v24_plus_v31": {
        "local_hf_retention": 0.36,
        "local_opponent_strength": 0.66,
        "publication": "scan_referenced",
        "publication_hf_retention": 1.0,
    },
    "direct_managed_projection": {
        "local_hf_retention": 0.0,
        "local_opponent_strength": 0.66,
        "publication": "direct",
        "publication_hf_retention": 0.0,
    },
    "direct_unmanaged_projection": {
        "local_hf_retention": 1.0,
        "local_opponent_strength": 1.0,
        "publication": "direct",
        "publication_hf_retention": 1.0,
    },
}


@contextmanager
def local_grain_policy(high_frequency_retention: float, strength: float):
    previous = (
        e.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION,
        e.PROJECTION_CHROMA_GRAIN_OPPONENT_STRENGTH,
    )
    try:
        e.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION = float(
            high_frequency_retention
        )
        e.PROJECTION_CHROMA_GRAIN_OPPONENT_STRENGTH = float(strength)
        yield
    finally:
        (
            e.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION,
            e.PROJECTION_CHROMA_GRAIN_OPPONENT_STRENGTH,
        ) = previous


def render_local_endpoint(
    engine: Emulsion5279Engine,
    negative: FormedNegative,
    frame: int,
    high_frequency_retention: float,
    strength: float,
) -> dict[str, np.ndarray]:
    with local_grain_policy(high_frequency_retention, strength):
        projection, scan, mean_projection, mean_scan = (
            e.reconstruct_density_pair_to_dual_display_v39(
                negative.mean_record_density,
                negative.formed_record_density,
                frame,
                1.0,
                "linear_rec709",
                return_mean_pair=True,
            )
        )
    return {
        "projection": projection,
        "scan": scan,
        "mean_projection": mean_projection,
        "mean_scan": mean_scan,
    }


def publish_policy(
    local: dict[str, np.ndarray], policy: dict[str, float | str]
) -> dict[str, np.ndarray]:
    if policy["publication"] == "direct":
        projection = local["projection"]
        mean_projection = local["mean_projection"]
    elif policy["publication"] == "scan_referenced":
        retention = float(policy["publication_hf_retention"])
        projection = adapt_frame_linear(
            local["projection"], local["scan"], retention
        )
        mean_projection = adapt_frame_linear(
            local["mean_projection"], local["mean_scan"], retention
        )
    else:
        raise ValueError(f"unknown publication: {policy['publication']}")
    return {
        "projection": np.asarray(projection, dtype=np.float32),
        "mean_projection": np.asarray(mean_projection, dtype=np.float32),
        "scan": local["scan"],
        "mean_scan": local["mean_scan"],
    }


def render_policies(
    engine: Emulsion5279Engine, negative: FormedNegative, frame: int
) -> dict[str, dict[str, np.ndarray]]:
    local_cache: dict[tuple[float, float], dict[str, np.ndarray]] = {}
    result: dict[str, dict[str, np.ndarray]] = {}
    for name, policy in POLICIES.items():
        key = (
            float(policy["local_hf_retention"]),
            float(policy["local_opponent_strength"]),
        )
        if key not in local_cache:
            local_cache[key] = render_local_endpoint(
                engine, negative, frame, key[0], key[1]
            )
        result[name] = publish_policy(local_cache[key], policy)
    scans = [row["scan"] for row in result.values()]
    if any(not np.array_equal(scans[0], scan) for scan in scans[1:]):
        raise AssertionError("projection-policy ablation changed the scan")
    return result


def luma_opponent_rms(residual: np.ndarray) -> dict[str, float]:
    rgb = np.asarray(residual, dtype=np.float64)
    luma = np.einsum("...c,c->...", rgb, LUMA)
    opponent = rgb - luma[..., None]
    return {
        "rgb": float(np.sqrt(np.mean(rgb * rgb))),
        "luma": float(np.sqrt(np.mean(luma * luma))),
        "opponent": float(np.sqrt(np.mean(opponent * opponent))),
        "opponent_over_luma": float(
            np.sqrt(np.mean(opponent * opponent))
            / max(np.sqrt(np.mean(luma * luma)), 1e-20)
        ),
    }


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    left = np.asarray(a, dtype=np.float64).ravel()
    right = np.asarray(b, dtype=np.float64).ravel()
    left -= np.mean(left)
    right -= np.mean(right)
    denominator = np.sqrt(np.sum(left * left) * np.sum(right * right))
    return float(np.sum(left * right) / max(denominator, 1e-30))


def mean_relative_tail_or_none(
    formed: np.ndarray, mean: np.ndarray
) -> dict[str, float | int] | None:
    """V77's dark-tail diagnostic is undefined for a bright uniform field."""
    mean_signal = np.asarray(e.srgb_encode(mean), dtype=np.float32)
    mean_luma = np.einsum("...c,c->...", mean_signal, LUMA)
    if not np.any(mean_luma[2:-2, 2:-2] < 0.18):
        return None
    return measure_mean_relative_grain_tail(formed, mean)


def describe_policy(
    row: dict[str, np.ndarray], *, crop: int | tuple[int, int] | None = None
) -> dict[str, object]:
    formed = row["projection"]
    mean = row["mean_projection"]
    scan = row["scan"]
    mean_scan = row["mean_scan"]
    projection_grain = formed - mean
    scan_grain = scan - mean_scan
    if isinstance(crop, int):
        projection_grain = centred_crop(projection_grain, crop)
        scan_grain = centred_crop(scan_grain, crop)
    elif crop is not None:
        projection_grain = centred_crop_rect(projection_grain, *crop)
        scan_grain = centred_crop_rect(scan_grain, *crop)
    width = projection_grain.shape[1]
    pixels_per_mm = width / FRAME_WIDTH_MM
    projection_luma = np.einsum("...c,c->...", projection_grain, LUMA)
    scan_luma = np.einsum("...c,c->...", scan_grain, LUMA)
    projection_opponent = projection_grain - projection_luma[..., None]
    scan_opponent = scan_grain - scan_luma[..., None]
    return {
        "grain_rms": luma_opponent_rms(projection_grain),
        "frequency": describe_rgb_residual(projection_grain, pixels_per_mm),
        "projection_scan_grain_correlation": {
            "luma": correlation(projection_luma, scan_luma),
            "opponent": correlation(projection_opponent, scan_opponent),
        },
        "deterministic_projection_vs_scan": difference_metrics(mean, mean_scan),
        "formed_projection_vs_scan": difference_metrics(formed, scan),
        "mean_relative_colour_tail": mean_relative_tail_or_none(formed, mean),
    }


def describe_scale_integrated(row: dict[str, np.ndarray]) -> dict[str, object]:
    integrated = {
        key: exact_integer_area(row[key], 3)
        for key in ("projection", "mean_projection", "scan", "mean_scan")
    }
    return describe_policy(integrated)


def exact_scale_retention(row: dict[str, np.ndarray]) -> dict[str, float]:
    native = luma_opponent_rms(row["projection"] - row["mean_projection"])
    formed_2k = exact_integer_area(row["projection"], 3)
    mean_2k = exact_integer_area(row["mean_projection"], 3)
    integrated = luma_opponent_rms(formed_2k - mean_2k)
    return {
        key: float(integrated[key] / max(native[key], 1e-20))
        for key in ("rgb", "luma", "opponent")
    }


def rms_ratio(
    candidate: dict[str, object], reference: dict[str, object]
) -> dict[str, float]:
    candidate_rms = candidate["grain_rms"]
    reference_rms = reference["grain_rms"]
    assert isinstance(candidate_rms, dict) and isinstance(reference_rms, dict)
    return {
        key: float(candidate_rms[key] / max(reference_rms[key], 1e-20))
        for key in ("rgb", "luma", "opponent", "opponent_over_luma")
    }


def audit_negative(
    engine: Emulsion5279Engine,
    negative: FormedNegative,
    frame: int,
    *,
    crop: int | tuple[int, int] | None,
) -> dict[str, object]:
    rendered = render_policies(engine, negative, frame)
    native = {
        name: describe_policy(row, crop=crop) for name, row in rendered.items()
    }
    integrated = {
        name: describe_scale_integrated(row) for name, row in rendered.items()
    }
    native_reference = native["current_v72_managed"]
    integrated_reference = integrated["current_v72_managed"]
    reference = rendered["current_v72_managed"]
    changes = {
        name: {
            "formed_projection": difference_metrics(
                reference["projection"], row["projection"]
            ),
            "deterministic_mean": difference_metrics(
                reference["mean_projection"], row["mean_projection"]
            ),
        }
        for name, row in rendered.items()
        if name != "current_v72_managed"
    }
    return {
        "native": native,
        "exact_3x3_scale_integrated": integrated,
        "exact_3x3_scale_retention": {
            name: exact_scale_retention(row) for name, row in rendered.items()
        },
        "endpoint_over_current_v72_grain_rms": {
            name: {
                "native": rms_ratio(row, native_reference),
                "scale_integrated": rms_ratio(
                    integrated[name], integrated_reference
                ),
            }
            for name, row in native.items()
        },
        "change_from_current_v72": changes,
        "scan_identity_maximum_absolute": float(
            max(
                np.max(np.abs(row["scan"] - reference["scan"]))
                for row in rendered.values()
            )
        ),
    }


def measure(input_path: Path, decoder_path: Path) -> dict[str, object]:
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
        with ProResRawDecoder(decoder_path, input_path, 0, 1) as decoder:
            frame, raw = next(iter(decoder))
        real_negative = engine.form_negative(raw, frame)
        real = audit_negative(engine, real_negative, frame, crop=1536)
        uniform = {
            str(log_exposure): audit_negative(
                engine,
                uniform_negative(log_exposure, 7900 + index * 100),
                7900 + index * 100,
                crop=(144, 5616),
            )
            for index, log_exposure in enumerate((-1.0, 0.0))
        }
    finally:
        engine.close()

    real_native = real["native"]
    current_tail = real_native["current_v72_managed"][
        "mean_relative_colour_tail"
    ]
    v31_tail = real_native["restore_v31_publication_only"][
        "mean_relative_colour_tail"
    ]
    v24_tail = real_native["historical_v24_plus_v31"][
        "mean_relative_colour_tail"
    ]
    unmanaged_tail = real_native["direct_unmanaged_projection"][
        "mean_relative_colour_tail"
    ]
    assert all(
        isinstance(item, dict)
        for item in (current_tail, v31_tail, v24_tail, unmanaged_tail)
    )

    return {
        "audit": "V79 projection grain and publication-policy ownership",
        "profile": "V72 evidence-minimal record formation",
        "image_change": "none; endpoint ablation only",
        "input": str(input_path),
        "fixed_boundaries": [
            "one identical formed V72 negative per scene",
            "archive_pointwise stochastic projection observer",
            "current 5279 MTF, DIR, density and 2383 spectral observer",
            "identical scan branch",
            "no codec in this ownership audit",
        ],
        "policy_endpoints": POLICIES,
        "real_T020": real,
        "uniform_log_exposure": uniform,
        "causal_findings": {
            "T020_isolated_mean_relative_opponent_events_gt_0_08": {
                "current_v72_managed": current_tail[
                    "isolated_gt_0_08_count"
                ],
                "restore_v31_publication_only": v31_tail[
                    "isolated_gt_0_08_count"
                ],
                "historical_v24_plus_v31": v24_tail[
                    "isolated_gt_0_08_count"
                ],
                "direct_unmanaged_projection": unmanaged_tail[
                    "isolated_gt_0_08_count"
                ],
            },
            "interpretation": (
                "Both V40 boundaries suppress a colour-impulse failure that "
                "still exists in the current underidentified cross-record "
                "model. The publication adapter also changes deterministic "
                "colour, so it cannot be described as grain management alone."
            ),
        },
        "classification": {
            "current_local_projection_grain_finish": (
                "historical managed display-space luma/opponent policy; Kodak "
                "does not publish the needed cross-record projection NPS"
            ),
            "current_projection_colour_publication": (
                "historical scan-referenced monitor policy; not a measured "
                "5279, 2383, projector or scanner property"
            ),
            "direct_unmanaged_projection": (
                "mathematical upper endpoint, not a claim of physical truth"
            ),
        },
        "decision_rule": (
            "Do not promote an endpoint because it looks richer or more filmic. "
            "Use the ablation to identify causal ownership, retain all endpoints "
            "as uncertainty bounds, and require measured 5279 cross-record NPS "
            "or matched negative/2383 projection data before choosing a physical "
            "colour-frequency covariance."
        ),
        "decision": (
            "Retain the current V72 managed projection for released images as "
            "a defect-containment boundary, but explicitly withdraw any claim "
            "that its 0.62/0.66/zero-retention coefficients or scan-referenced "
            "publication are measured 5279/2383 projection physics. Do not "
            "restore V24/V31 or the unmanaged endpoint. The next physical "
            "advance must identify the missing cross-record covariance before "
            "the display-space safety boundary can be reduced."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode")
    )
    args = parser.parse_args()
    report = measure(args.input, args.decoder)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
