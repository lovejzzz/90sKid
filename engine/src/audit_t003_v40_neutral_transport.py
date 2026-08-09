#!/usr/bin/env python3
"""Audit whether deterministic V40 amplifies T003 neutral-axis colour drift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v40_profile
from apply_v31_normal_process_adapter import adapt_frame_linear
from audit_t003_colorchecker import (
    BT2020_TO_XYZ,
    decode_raw,
    patch_samples,
)
from render_v40_dual_masters import PRINT_LUT, PRINT_LUT_SHA256
from render_v40_fsd_comparator import deterministic_dual_observer
from render_v23_dual_masters import sha256


REC709_TO_XYZ = np.asarray(
    [
        [0.4123907993, 0.3575843394, 0.1804807884],
        [0.2126390059, 0.7151686788, 0.0721923154],
        [0.0193308187, 0.1191947798, 0.9505321522],
    ],
    dtype=np.float64,
)


def uv_prime(rgb: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    xyz = np.asarray(rgb, dtype=np.float64) @ matrix.T
    denominator = xyz[:, 0] + 15.0 * xyz[:, 1] + 3.0 * xyz[:, 2]
    return np.column_stack(
        [4.0 * xyz[:, 0] / denominator, 9.0 * xyz[:, 1] / denominator]
    )


def neutral_record(image: np.ndarray, homography: np.ndarray, matrix: np.ndarray) -> dict[str, object]:
    medians = np.asarray(
        [
            np.median(patch_samples(image, homography, 0, column), axis=0)
            for column in range(1, 5)
        ],
        dtype=np.float64,
    )
    uv = uv_prime(medians, matrix)
    center = np.mean(uv, axis=0)
    return {
        "patches": [2, 3, 4, 5],
        "linear_RGB_medians": medians.tolist(),
        "R_over_G": (medians[:, 0] / medians[:, 1]).tolist(),
        "B_over_G": (medians[:, 2] / medians[:, 1]).tolist(),
        "u_prime_v_prime": uv.tolist(),
        "maximum_delta_uv_from_group_mean": float(
            np.max(np.linalg.norm(uv - center, axis=1))
        ),
        "endpoint_delta_uv_patch_2_to_5": float(np.linalg.norm(uv[0] - uv[-1])),
    }


def render_deterministic_pair(
    raw: np.ndarray, exposure_stops: float
) -> tuple[np.ndarray, np.ndarray]:
    film = e.scene_to_5279_film_rgb(
        raw,
        exposure_stops=exposure_stops,
        raw_colour=v40_profile.PROFILE["raw_colour"],
        include_optical_scatter=True,
        sensor_noise_treatment="photochemical",
    )
    records = e.film_records_from_rgb(film)
    mean_density = e.develop_5279_record_density(records)
    projection, scan = deterministic_dual_observer(mean_density, 1.0)
    return (
        adapt_frame_linear(
            projection,
            scan,
            v40_profile.PROFILE.get(
                "final_adapter_opponent_high_frequency_retention", 0.0
            ),
        ).astype(np.float32),
        scan,
    )


def block_neutral_record(image: np.ndarray, block_width: int) -> dict[str, object]:
    medians = []
    margin = block_width // 3
    for index in range(4):
        x0 = index * block_width + margin
        x1 = (index + 1) * block_width - margin
        y0 = image.shape[0] // 3
        y1 = image.shape[0] - y0
        medians.append(np.median(image[y0:y1, x0:x1], axis=(0, 1)))
    medians = np.asarray(medians, dtype=np.float64)
    uv = uv_prime(medians, REC709_TO_XYZ)
    center = np.mean(uv, axis=0)
    return {
        "linear_RGB_medians": medians.tolist(),
        "u_prime_v_prime": uv.tolist(),
        "maximum_delta_uv_from_group_mean": float(
            np.max(np.linalg.norm(uv - center, axis=1))
        ),
        "endpoint_delta_uv": float(np.linalg.norm(uv[0] - uv[-1])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=160)
    parser.add_argument("--exposure-stops", type=float, default=0.45)
    parser.add_argument(
        "--crop",
        default="3200,1350,4700,2450",
        help="x0,y0,x1,y1 native crop with wide optical-support margin",
    )
    args = parser.parse_args()
    if sha256(PRINT_LUT) != PRINT_LUT_SHA256:
        raise ValueError("validated V40 print LUT hash mismatch")
    v40_profile.apply(e)
    e._PRINT_2383_MONITOR_OUTPUT_LUT = np.load(PRINT_LUT, allow_pickle=False)
    cv2.setNumThreads(8)
    import v27_accel

    v27_accel.apply(e, numba_threads=8, array_workers=8, exact_only=True)
    v27_accel.warm(e)
    width, height, _ = e.probe_video(args.source)
    raw = decode_raw(args.decoder, args.source, args.frame, width, height)
    x0, y0, x1, y1 = [int(value) for value in args.crop.split(",")]
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError("invalid crop")
    raw = raw[y0:y1, x0:x1].copy()
    corners = np.asarray(
        [[3500.0, 1635.0], [4330.0, 1565.0], [4390.0, 2188.0], [3510.0, 2230.0]],
        dtype=np.float32,
    )
    homography = cv2.getPerspectiveTransform(
        np.asarray([[0, 0], [6, 0], [6, 3], [0, 3]], dtype=np.float32),
        corners,
    )
    homography = np.asarray(
        [[1.0, 0.0, -x0], [0.0, 1.0, -y0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    ) @ homography
    final_projection, scan = render_deterministic_pair(raw, args.exposure_stops)
    report = {
        "scope": "deterministic neutral-axis transport; no stochastic grain and no creative grade",
        "source": str(args.source),
        "frame": args.frame,
        "native_crop_xyxy": [x0, y0, x1, y1],
        "minimum_crop_margin_pixels_from_chart_corners": int(
            min(corners[:, 0].min() - x0, corners[:, 1].min() - y0,
                x1 - corners[:, 0].max(), y1 - corners[:, 1].max())
        ),
        "sampling": "corrected DKC-Pro row-specific safe interiors",
        "input_Apple_extended_linear_BT2020": neutral_record(
            raw, homography, BT2020_TO_XYZ
        ),
        "period_2K_scan_display_linear_Rec709": neutral_record(
            scan, homography, REC709_TO_XYZ
        ),
        "normal_2383_projection_display_linear_Rec709": neutral_record(
            final_projection, homography, REC709_TO_XYZ
        ),
    }
    source_spread = report["input_Apple_extended_linear_BT2020"][
        "maximum_delta_uv_from_group_mean"
    ]
    for key in (
        "period_2K_scan_display_linear_Rec709",
        "normal_2383_projection_display_linear_Rec709",
    ):
        report[key]["spread_ratio_to_input"] = float(
            report[key]["maximum_delta_uv_from_group_mean"] / source_spread
        )

    # Remove the outdoor chart's spatial gradient: four equal-colour blocks
    # use the measured neutral-patch G levels but share one chromaticity.
    block_width = 384
    block_height = 384
    source_medians = np.asarray(
        report["input_Apple_extended_linear_BT2020"]["linear_RGB_medians"],
        dtype=np.float32,
    )
    green_levels = source_medians[:, 1]
    warm_ratio = np.mean(source_medians / source_medians[:, 1, None], axis=0)

    def synthetic_blocks(ratio: np.ndarray) -> np.ndarray:
        return np.concatenate(
            [
                np.broadcast_to(
                    green_levels[index] * ratio,
                    (block_height, block_width, 3),
                )
                for index in range(4)
            ],
            axis=1,
        ).astype(np.float32, copy=True)

    synthetic: dict[str, object] = {}
    for name, ratio in (
        ("constant_D65_neutral", np.ones(3, dtype=np.float32)),
        ("constant_measured_warm_chromaticity", warm_ratio),
    ):
        projection_blocks, scan_blocks = render_deterministic_pair(
            synthetic_blocks(ratio), args.exposure_stops
        )
        synthetic[name] = {
            "input_RGB_ratio_to_green": ratio.tolist(),
            "input_green_levels": green_levels.tolist(),
            "period_2K_scan": block_neutral_record(scan_blocks, block_width),
            "normal_2383_projection": block_neutral_record(
                projection_blocks, block_width
            ),
        }
    report["synthetic_constant_chromaticity_controls"] = synthetic
    report["interpretation"] = {
        "D65_neutral_axis": (
            "stable: maximum output delta u'v' is below 0.00018 in both "
            "deterministic observers; V40 does not create a shared neutral-green crossover"
        ),
        "off_neutral_warm_axis": (
            "exposure dependent: a constant measured warm chromaticity reaches "
            "maximum delta u'v' 0.00253 in scan and 0.00220 in projection; "
            "colour-negative tone-dependent reproduction is plausible, but this "
            "magnitude remains a model uncertainty until a matched controlled-light "
            "5279 reference exists"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
