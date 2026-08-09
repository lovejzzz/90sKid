#!/usr/bin/env python3
"""Track the T003 DKC-Pro through time to test single-frame conclusions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
from audit_t003_colorchecker import (
    BT2020_TO_XYZ,
    PATCHES,
    decode_raw,
    patch_samples,
)


REFERENCE_FRAME = 160
REFERENCE_CORNERS = np.asarray(
    [[3500.0, 1635.0], [4330.0, 1565.0], [4390.0, 2188.0], [3510.0, 2230.0]],
    dtype=np.float32,
)
IDEAL_CORNERS = np.asarray([[0, 0], [6, 0], [6, 3], [0, 3]], dtype=np.float32)
SCALE = 0.5


def tracking_gray(raw: np.ndarray) -> np.ndarray:
    display = e.srgb_encode(np.clip(raw, 0.0, 1.0))
    gray = cv2.cvtColor(display, cv2.COLOR_RGB2GRAY)
    return np.rint(
        cv2.resize(gray, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)
        * 255.0
    ).astype(np.uint8)


def frame_measurement(raw: np.ndarray, homography: np.ndarray) -> dict[str, object]:
    medians = []
    for index in range(18):
        row, column = divmod(index, 6)
        medians.append(np.median(patch_samples(raw, homography, row, column), axis=0))
    medians = np.asarray(medians, dtype=np.float64)
    ratios = np.column_stack(
        [medians[:, 0] / medians[:, 1], medians[:, 2] / medians[:, 1]]
    )
    reference_y = np.asarray(
        [((PATCHES[index][1] + 16.0) / 116.0) ** 3 for index in range(1, 5)]
    )
    measured_y = medians[1:5] @ BT2020_TO_XYZ[1]
    scale = measured_y / reference_y
    slope, intercept = np.polyfit(np.log(reference_y), np.log(measured_y), 1)
    return {
        "recommended_neutral_2_to_4_mean_R_over_G": float(np.mean(ratios[1:4, 0])),
        "recommended_neutral_2_to_4_mean_B_over_G": float(np.mean(ratios[1:4, 1])),
        "recommended_neutral_2_to_4_R_over_G_span_percent": float(np.ptp(ratios[1:4, 0]) / np.mean(ratios[1:4, 0]) * 100.0),
        "recommended_neutral_2_to_4_B_over_G_span_percent": float(np.ptp(ratios[1:4, 1]) / np.mean(ratios[1:4, 1]) * 100.0),
        "measured_Y_over_reference_Y_patches_2_to_5": scale.tolist(),
        "scale_span_stops": float(np.log2(scale.max() / scale.min())),
        "log_slope_patches_2_to_5": float(slope),
        "log_intercept_patches_2_to_5": float(intercept),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    args = parser.parse_args()
    cv2.setNumThreads(2)
    width, height, _ = e.probe_video(args.source)
    ideal_grid = np.asarray(
        [[x, y] for y in range(4) for x in range(7)], dtype=np.float32
    )
    reference_h = cv2.getPerspectiveTransform(IDEAL_CORNERS, REFERENCE_CORNERS)
    reference_points = cv2.perspectiveTransform(
        ideal_grid[None], reference_h
    )[0] * SCALE
    raw_reference = decode_raw(
        args.decoder, args.source, REFERENCE_FRAME, width, height
    )
    gray_reference = tracking_gray(raw_reference)
    records: dict[int, dict[str, object]] = {
        REFERENCE_FRAME: {
            "homography": reference_h.tolist(),
            "tracking_inliers": len(ideal_grid),
            **frame_measurement(raw_reference, reference_h),
        }
    }

    for targets in (
        list(range(150, 79, -10)),
        list(range(170, 201, 10)),
    ):
        previous_gray = gray_reference
        previous_points = reference_points.copy()
        for frame in targets:
            raw = decode_raw(args.decoder, args.source, frame, width, height)
            gray = tracking_gray(raw)
            forward, status, _ = cv2.calcOpticalFlowPyrLK(
                previous_gray,
                gray,
                previous_points[:, None],
                None,
                winSize=(41, 41),
                maxLevel=4,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.005),
            )
            backward, back_status, _ = cv2.calcOpticalFlowPyrLK(
                gray,
                previous_gray,
                forward,
                None,
                winSize=(41, 41),
                maxLevel=4,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.005),
            )
            forward = forward[:, 0]
            backward = backward[:, 0]
            valid = (
                status[:, 0].astype(bool)
                & back_status[:, 0].astype(bool)
                & (np.linalg.norm(backward - previous_points, axis=1) < 1.5)
            )
            if int(np.sum(valid)) < 8:
                raise RuntimeError(f"only {int(np.sum(valid))} tracked points at frame {frame}")
            homography, inlier_mask = cv2.findHomography(
                ideal_grid[valid], forward[valid] / SCALE, cv2.RANSAC, 4.0
            )
            if homography is None:
                raise RuntimeError(f"homography failed at frame {frame}")
            inliers = int(np.sum(inlier_mask))
            records[frame] = {
                "homography": homography.tolist(),
                "tracking_inliers": inliers,
                **frame_measurement(raw, homography),
            }
            previous_gray = gray
            previous_points = cv2.perspectiveTransform(
                ideal_grid[None], homography.astype(np.float32)
            )[0] * SCALE

    selected = [80, 100, 120, 140, 160, 180, 200]
    rows = [records[frame] for frame in selected]
    report = {
        "source": str(args.source),
        "frames": {str(frame): records[frame] for frame in selected},
        "summary": {
            "frames": selected,
            "R_over_G_mean_min_max": [
                float(np.mean([row["recommended_neutral_2_to_4_mean_R_over_G"] for row in rows])),
                float(np.min([row["recommended_neutral_2_to_4_mean_R_over_G"] for row in rows])),
                float(np.max([row["recommended_neutral_2_to_4_mean_R_over_G"] for row in rows])),
            ],
            "B_over_G_mean_min_max": [
                float(np.mean([row["recommended_neutral_2_to_4_mean_B_over_G"] for row in rows])),
                float(np.min([row["recommended_neutral_2_to_4_mean_B_over_G"] for row in rows])),
                float(np.max([row["recommended_neutral_2_to_4_mean_B_over_G"] for row in rows])),
            ],
            "gray_scale_span_stops_mean_min_max": [
                float(np.mean([row["scale_span_stops"] for row in rows])),
                float(np.min([row["scale_span_stops"] for row in rows])),
                float(np.max([row["scale_span_stops"] for row in rows])),
            ],
            "log_slope_mean_min_max": [
                float(np.mean([row["log_slope_patches_2_to_5"] for row in rows])),
                float(np.min([row["log_slope_patches_2_to_5"] for row in rows])),
                float(np.max([row["log_slope_patches_2_to_5"] for row in rows])),
            ],
            "interpretation": (
                "multi-frame consistency can confirm a stable observation, but patch "
                "lightness remains spatially ordered; it still cannot identify camera "
                "gamma independently from card reflectance/illumination geometry"
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
