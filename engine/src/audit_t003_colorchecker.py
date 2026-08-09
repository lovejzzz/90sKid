#!/usr/bin/env python3
"""Measure the DGK DKC-Pro chart in a ProRes RAW frame.

This is an input-boundary audit, not an automatic white-balance or camera
profile.  The chart was photographed in a real scene, so the report separates
measured neutral-axis/linearity evidence from unsupported illuminant claims.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

import emulsion_experiment as e
import v40_profile
from render_v30_camera_baseline import (
    DEFAULT_V709_LUT,
    V709_LEGAL_BLACK,
    V709_LEGAL_WHITE,
    load_cube,
)


PATCHES = [
    ("white", 97, 0, 1), ("gray_73", 73, 0, 0),
    ("gray_62", 62, 0, 0), ("gray_50", 50, 0, 0),
    ("gray_38", 38, 0, 0), ("black", 23, 0, 0),
    ("red", 48, 59, 39), ("yellow", 92, 1, 95),
    ("green", 64, -40, 54), ("cyan", 57, -41, -42),
    ("blue", 18, -3, -25), ("magenta", 49, 60, -3),
    ("CIE_TSC_01", 41, 51, 26), ("CIE_TSC_02", 61, 29, 57),
    ("CIE_TSC_06", 52, -24, -24), ("CIE_TSC_08", 52, 47, -14),
    ("CIE_TSC_09", 69, 14, 17), ("CIE_TSC_10", 64, 12, 17),
]

BT2020_TO_XYZ = np.asarray(
    [[0.6369580483, 0.1446169036, 0.1688809752],
     [0.2627002120, 0.6779980715, 0.0593017165],
     [0.0000000000, 0.0280726930, 1.0609850577]],
    dtype=np.float64,
)
D50_XYZ = np.asarray([0.96422, 1.0, 0.82521], dtype=np.float64)
BRADFORD = np.asarray(
    [[0.8951, 0.2664, -0.1614],
     [-0.7502, 1.7135, 0.0367],
     [0.0389, -0.0685, 1.0296]],
    dtype=np.float64,
)


def lab_to_xyz_d50(lab: np.ndarray) -> np.ndarray:
    lightness, a, b = np.asarray(lab, dtype=np.float64)
    fy = (lightness + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    delta = 6.0 / 29.0
    inverse = lambda value: value**3 if value > delta else 3.0 * delta**2 * (value - 4.0 / 29.0)
    return D50_XYZ * np.asarray([inverse(fx), inverse(fy), inverse(fz)])


def xyz_to_lab_d50(xyz: np.ndarray) -> np.ndarray:
    delta = 6.0 / 29.0
    threshold = delta**3
    values = np.asarray(xyz, dtype=np.float64) / D50_XYZ
    transformed = np.where(
        values > threshold,
        np.cbrt(values),
        values / (3.0 * delta**2) + 4.0 / 29.0,
    )
    fx, fy, fz = transformed
    return np.asarray(
        [116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)]
    )


def colour_residual_diagnostic(records: list[dict[str, object]]) -> dict[str, object]:
    """Probe residual hue/chroma after neutral adaptation.

    DGK publishes Lab triplets but not the measurement illuminant/observer in
    this guide.  D50/Bradford is therefore an explicit diagnostic assumption,
    never a camera-profile calibration.
    """
    decoded = np.asarray(
        [record["decoded_linear_bt2020_median"] for record in records],
        dtype=np.float64,
    )
    measured_xyz = decoded @ BT2020_TO_XYZ.T
    # The manufacturer recommends patches 2, 3 and 4 for RAW white balance.
    neutral_xyz = measured_xyz[1:4]
    source_white = np.mean(neutral_xyz / neutral_xyz[:, 1, None], axis=0)
    cone_source = BRADFORD @ source_white
    cone_target = BRADFORD @ D50_XYZ
    adaptation = (
        np.linalg.inv(BRADFORD)
        @ np.diag(cone_target / cone_source)
        @ BRADFORD
    )
    adapted = (adaptation @ measured_xyz.T).T
    reference_lab = np.asarray(
        [record["manufacturer_CIELAB_as_published"] for record in records],
        dtype=np.float64,
    )
    reference_xyz = np.asarray([lab_to_xyz_d50(lab) for lab in reference_lab])

    # Isolate chromaticity from the chart's measurable illumination gradient.
    normalized = adapted * (reference_xyz[:, 1] / adapted[:, 1])[:, None]
    measured_lab = np.asarray([xyz_to_lab_d50(xyz) for xyz in normalized])
    ref_hue = np.degrees(np.arctan2(reference_lab[:, 2], reference_lab[:, 1]))
    measured_hue = np.degrees(np.arctan2(measured_lab[:, 2], measured_lab[:, 1]))
    hue_delta = (measured_hue - ref_hue + 180.0) % 360.0 - 180.0
    ref_chroma = np.linalg.norm(reference_lab[:, 1:3], axis=1)
    measured_chroma = np.linalg.norm(measured_lab[:, 1:3], axis=1)

    def group(indices: np.ndarray) -> dict[str, float]:
        return {
            "median_absolute_hue_error_degrees": float(np.median(np.abs(hue_delta[indices]))),
            "maximum_absolute_hue_error_degrees": float(np.max(np.abs(hue_delta[indices]))),
            "median_chroma_ratio": float(np.median(measured_chroma[indices] / ref_chroma[indices])),
        }

    # A fixed 3x3 should generalize between the synthetic primary row and the
    # natural-colour row.  Fit chromaticity on one group and test the other.
    chroma_measured = adapted / adapted[:, 1, None]
    chroma_reference = reference_xyz / reference_xyz[:, 1, None]

    def cross_fit(train: np.ndarray, test: np.ndarray) -> dict[str, float]:
        matrix, *_ = np.linalg.lstsq(
            chroma_measured[train], chroma_reference[train], rcond=None
        )
        output_hue: list[float] = []
        output_chroma: list[float] = []
        for index in test:
            mapped = chroma_measured[index] @ matrix
            mapped *= reference_xyz[index, 1] / mapped[1]
            lab = xyz_to_lab_d50(mapped)
            delta = (
                np.degrees(np.arctan2(lab[2], lab[1]))
                - ref_hue[index] + 180.0
            ) % 360.0 - 180.0
            output_hue.append(abs(float(delta)))
            output_chroma.append(float(np.linalg.norm(lab[1:3]) / ref_chroma[index]))
        return {
            "test_median_absolute_hue_error_degrees": float(np.median(output_hue)),
            "test_maximum_absolute_hue_error_degrees": float(np.max(output_hue)),
            "test_median_chroma_ratio": float(np.median(output_chroma)),
        }

    primary = np.arange(6, 12)
    natural = np.arange(12, 18)
    return {
        "assumption": (
            "D50 reference plus Bradford neutral adaptation for diagnosis only; "
            "the DGK guide does not state measurement illuminant/observer"
        ),
        "estimated_source_white_XYZ_Y1_from_patches_2_to_4": source_white.tolist(),
        "synthetic_primary_patches_7_to_12": group(primary),
        "natural_colour_patches_13_to_18": group(natural),
        "matrix_fit_naturals_test_primaries": cross_fit(natural, primary),
        "matrix_fit_primaries_test_naturals": cross_fit(primary, natural),
        "interpretation": (
            "after excluding the DKC-Pro title strip, cross-group 3x3 fits "
            "generalize moderately in hue; an input-characterization residual is "
            "plausible but cannot be fitted from this outdoor chart because the "
            "reference illuminant/observer and scene SPD are not identified"
        ),
    }


def decode_raw(decoder: Path, source: Path, frame: int, width: int, height: int) -> np.ndarray:
    payload = subprocess.check_output(
        [str(decoder), str(source), str(frame), "1"], stderr=subprocess.DEVNULL
    )
    expected = width * height * 3 * 4
    if len(payload) != expected:
        raise RuntimeError(f"short RAW decode: {len(payload)} != {expected}")
    return np.frombuffer(payload, dtype="<f4").reshape(height, width, 3).copy()


def source_recording_metadata(source: Path) -> dict[str, object]:
    probe = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_format", "-of", "json", str(source)],
        text=True,
    ))
    tags = probe.get("format", {}).get("tags", {})
    return {
        "camera_manufacturer": tags.get("com.apple.proapps.manufacturer"),
        "camera_model": tags.get("com.apple.proapps.modelname"),
        "white_balance": tags.get("org.smpte.rdd18.camera.whitebalance"),
        "ISO": tags.get("org.smpte.rdd18.camera.isosensitivity"),
        "intermediate_OETF": tags.get("com.atomos.raw.intermediate_oetf"),
        "intermediate_gamut": tags.get("com.atomos.raw.intermediate_gamut"),
        "recorder": tags.get("encoder"),
    }


PATCH_X_INTERIOR = (0.35, 0.65)
# DKC-Pro is not an equal-height 3 x 6 grid. The upper gray row is taller and
# a printed title strip precedes the middle row. Treating row centres as
# y={0.5,1.5,2.5} contaminated patches 7-12 with that dark strip. These
# rectified-grid interiors were checked at native resolution and exclude text,
# dividers and outer borders.
PATCH_Y_INTERIORS = ((0.30, 0.68), (1.68, 1.94), (2.34, 2.66))


def patch_samples(image: np.ndarray, homography: np.ndarray, row: int, column: int) -> np.ndarray:
    x = np.linspace(column + PATCH_X_INTERIOR[0], column + PATCH_X_INTERIOR[1], 15, dtype=np.float32)
    y = np.linspace(*PATCH_Y_INTERIORS[row], 15, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    points = np.stack([xx.ravel(), yy.ravel()], axis=-1)[None]
    mapped = cv2.perspectiveTransform(points, homography)[0]
    x = np.clip(np.rint(mapped[:, 0]).astype(np.int32), 0, image.shape[1] - 1)
    y = np.clip(np.rint(mapped[:, 1]).astype(np.int32), 0, image.shape[0] - 1)
    return image[y, x]


def uv_prime_from_bt2020(rgb: np.ndarray) -> tuple[float, float]:
    xyz = BT2020_TO_XYZ @ np.asarray(rgb, dtype=np.float64)
    denominator = xyz[0] + 15.0 * xyz[1] + 3.0 * xyz[2]
    return float(4.0 * xyz[0] / denominator), float(9.0 * xyz[1] / denominator)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=160)
    parser.add_argument(
        "--corners",
        default="3500,1635;4330,1565;4390,2188;3510,2230",
        help="patch-grid TL;TR;BR;BL in native pixels",
    )
    args = parser.parse_args()
    v40_profile.apply(e)
    width, height, _ = e.probe_video(args.source)
    raw = decode_raw(args.decoder, args.source, args.frame, width, height)
    corners = np.asarray(
        [[float(v) for v in pair.split(",")] for pair in args.corners.split(";")],
        dtype=np.float32,
    )
    ideal = np.asarray([[0, 0], [6, 0], [6, 3], [0, 3]], dtype=np.float32)
    homography = cv2.getPerspectiveTransform(ideal, corners)

    vgamut = e.bt2020_to_panasonic_vgamut(raw)
    vlog = e.vlog_encode(vgamut)
    legal = e.apply_rgb_cube_lut(vlog, load_cube(DEFAULT_V709_LUT))
    v709 = np.clip(
        (legal - V709_LEGAL_BLACK) / (V709_LEGAL_WHITE - V709_LEGAL_BLACK),
        0.0, 1.0,
    ).astype(np.float32)

    records = []
    neutral_reflectance = []
    neutral_measured = []
    d65_uv = uv_prime_from_bt2020(np.ones(3))
    for index, (name, lab_l, lab_a, lab_b) in enumerate(PATCHES):
        row, column = divmod(index, 6)
        raw_values = patch_samples(raw, homography, row, column)
        v709_values = patch_samples(v709, homography, row, column)
        raw_median = np.median(raw_values, axis=0)
        raw_mad = np.median(np.abs(raw_values - raw_median), axis=0)
        raw_p05 = np.quantile(raw_values, 0.05, axis=0)
        raw_p95 = np.quantile(raw_values, 0.95, axis=0)
        v709_median = np.median(v709_values, axis=0)
        u, v = uv_prime_from_bt2020(raw_median)
        record = {
            "patch": index + 1,
            "name": name,
            "manufacturer_CIELAB_as_published": [lab_l, lab_a, lab_b],
            "decoded_linear_bt2020_median": [float(x) for x in raw_median],
            "decoded_linear_bt2020_MAD_percent_of_median": [
                float(x) for x in (raw_mad / raw_median * 100.0)
            ],
            "decoded_linear_bt2020_p05_to_p95_percent_of_median": [
                float(x) for x in ((raw_p95 - raw_p05) / raw_median * 100.0)
            ],
            "decoded_linear_channel_ratios_R_over_G_B_over_G": [
                float(raw_median[0] / raw_median[1]),
                float(raw_median[2] / raw_median[1]),
            ],
            "decoded_linear_u_prime_v_prime": [u, v],
            "distance_from_D65_u_prime_v_prime": float(np.hypot(u - d65_uv[0], v - d65_uv[1])),
            "official_Panasonic_V709_encoded_median": [float(x) for x in v709_median],
        }
        records.append(record)
        if 1 < index + 1 < 6:
            fy = ((lab_l + 16.0) / 116.0) ** 3
            neutral_reflectance.append(fy)
            neutral_measured.append(float(BT2020_TO_XYZ[1] @ raw_median))

    slope, intercept = np.polyfit(
        np.log(np.asarray(neutral_reflectance)),
        np.log(np.asarray(neutral_measured)),
        1,
    )
    neutral = records[1:5]
    recommended_neutral = records[1:4]
    neutral_reference_y = np.asarray(neutral_reflectance, dtype=np.float64)
    neutral_measured_y = np.asarray(neutral_measured, dtype=np.float64)
    exposure_scale = neutral_measured_y / neutral_reference_y
    raw_patch_medians = np.asarray(
        [record["decoded_linear_bt2020_median"] for record in records],
        dtype=np.float64,
    )
    preclip_film_rgb = (
        raw_patch_medians * (2.0**0.45)
    ) @ e.AVFOUNDATION_BT2020_TO_FILM_RGB.T
    negative_locations = np.argwhere(preclip_film_rgb < 0.0)
    clipped_film_rgb = np.maximum(preclip_film_rgb, 0.0)
    signed_record_exposures = preclip_film_rgb @ e.FILM_RECORD_SENSITIVITY_RGB.T
    clipped_basis_record_exposures = clipped_film_rgb @ e.FILM_RECORD_SENSITIVITY_RGB.T
    basis_clip_record_delta = (
        clipped_basis_record_exposures / np.maximum(signed_record_exposures, 1e-8)
        - 1.0
    )
    negative_basis_patches = [
        {
            "patch": int(patch_index + 1),
            "name": records[int(patch_index)]["name"],
            "channel": "RGB"[int(channel_index)],
            "preclip_value": float(preclip_film_rgb[patch_index, channel_index]),
            "record_exposures_with_signed_basis": signed_record_exposures[patch_index].tolist(),
            "record_exposures_after_V40_basis_clip": clipped_basis_record_exposures[patch_index].tolist(),
            "record_exposure_delta_percent": (100.0 * basis_clip_record_delta[patch_index]).tolist(),
        }
        for patch_index, channel_index in negative_locations
    ]
    v709_medians = np.asarray(
        [record["official_Panasonic_V709_encoded_median"] for record in records],
        dtype=np.float64,
    )
    patch_mad_percent = np.asarray(
        [record["decoded_linear_bt2020_MAD_percent_of_median"] for record in records],
        dtype=np.float64,
    )
    report = {
        "source": str(args.source),
        "frame": args.frame,
        "dimensions": [width, height],
        "source_recording_metadata": source_recording_metadata(args.source),
        "target": "DGK Color Tools DKC-Pro 5 x 7",
        "target_reference": "manufacturer guide, DKC-Pro Colorimetry Data",
        "measurement_scope": (
            "diagnostic input-boundary evidence only; no automatic WB, camera matrix, "
            "or creative correction is inferred from this single real-world illuminant"
        ),
        "sampling_geometry": {
            "rectified_grid": "6 columns x nominal 3-height coordinate system",
            "x_interior_per_patch": list(PATCH_X_INTERIOR),
            "row_y_interiors": [list(values) for values in PATCH_Y_INTERIORS],
            "reason": (
                "DKC-Pro rows are not equal height; row-specific interiors exclude "
                "the printed title strip above patches 7-12 and all dividers"
            ),
        },
        "sampling_quality": {
            "median_channel_MAD_percent_of_patch_median": float(
                np.median(patch_mad_percent)
            ),
            "maximum_channel_MAD_percent_of_patch_median": float(
                np.max(patch_mad_percent)
            ),
            "all_patch_channels_MAD_below_6_percent": bool(
                np.all(patch_mad_percent < 6.0)
            ),
        },
        "patch_grid_corners_TL_TR_BR_BL": corners.tolist(),
        "decoded_neutral_axis_patches_2_to_5": {
            "mean_R_over_G": float(np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][0] for r in neutral])),
            "mean_B_over_G": float(np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][1] for r in neutral])),
            "mean_D65_delta_uv": float(np.mean([r["distance_from_D65_u_prime_v_prime"] for r in neutral])),
            "max_D65_delta_uv": float(np.max([r["distance_from_D65_u_prime_v_prime"] for r in neutral])),
        },
        "manufacturer_recommended_RAW_WB_patches_2_to_4": {
            "mean_R_over_G": float(np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][0] for r in recommended_neutral])),
            "mean_B_over_G": float(np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][1] for r in recommended_neutral])),
            "R_over_G_span_percent_of_mean": float(np.ptp([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][0] for r in recommended_neutral]) / np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][0] for r in recommended_neutral]) * 100.0),
            "B_over_G_span_percent_of_mean": float(np.ptp([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][1] for r in recommended_neutral]) / np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][1] for r in recommended_neutral]) * 100.0),
            "diagnostic_gains_relative_to_green_not_applied": [
                float(1.0 / np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][0] for r in recommended_neutral])),
                1.0,
                float(1.0 / np.mean([r["decoded_linear_channel_ratios_R_over_G_B_over_G"][1] for r in recommended_neutral])),
            ],
        },
        "decoded_linearity_fit_patches_2_to_5": {
            "log_measured_vs_log_reference_slope": float(slope),
            "log_exposure_intercept": float(intercept),
            "note": "slope 1 is the scene-linear ideal; four neutral patches reduce colour-patch/illuminant metamerism",
        },
        "gray_scale_identifiability": {
            "measured_Y_over_reference_Y_patches_2_to_5": exposure_scale.tolist(),
            "spatially_confounded_scale_span_stops": float(np.log2(exposure_scale.max() / exposure_scale.min())),
            "interpretation": (
                "gray lightness is ordered left-to-right on the same row, so the "
                "measured scale change cannot distinguish sensor gamma from an "
                "illumination/reflection gradient across the angled outdoor chart"
            ),
        },
        "highlight_and_V40_input_boundary": {
            "decoded_linear_white_patch_RGB": raw_patch_medians[0].tolist(),
            "decoded_linear_white_exceeds_unit_range_all_channels": bool(np.all(raw_patch_medians[0] > 1.0)),
            "Panasonic_V709_patch_channels_at_1_count": int(np.sum(v709_medians >= 1.0 - 1e-7)),
            "Panasonic_V709_patches_with_any_channel_at_1": [int(i + 1) for i in np.flatnonzero(np.any(v709_medians >= 1.0 - 1e-7, axis=1))],
            "balanced_film_basis_negative_channel_count_before_V40_clip": int(len(negative_locations)),
            "balanced_film_basis_negative_patches": negative_basis_patches,
            "signed_basis_record_exposure_negative_count": int(np.sum(signed_record_exposures < 0.0)),
            "V40_record_exposure_negative_count_after_basis_clip": int(np.sum(clipped_basis_record_exposures < 0.0)),
            "interpretation": (
                "RAW retains chart-white headroom. The saturated cyan patch creates "
                "one negative red component in the intermediate Rec.709-like film-light "
                "basis. V40 clips that component before record sensitivities, although "
                "the combined signed-basis record exposures would all remain positive; "
                "this is a real gamut-boundary model choice, not a RAW highlight clip. "
                "Only the official V-709 display witness reaches its endpoint."
            ),
        },
        "colour_residual_diagnostic": colour_residual_diagnostic(records),
        "patches": records,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "t003_dkc_pro_audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )

    overlay = np.rint(e.srgb_encode(np.clip(raw, 0.0, 1.0))[..., ::-1] * 255.0).astype(np.uint8)
    for index in range(18):
        row, column = divmod(index, 6)
        center_y = sum(PATCH_Y_INTERIORS[row]) * 0.5
        center = cv2.perspectiveTransform(
            np.asarray([[[column + 0.5, center_y]]], dtype=np.float32), homography
        )[0, 0]
        cv2.circle(overlay, tuple(np.rint(center).astype(int)), 25, (0, 255, 255), 5)
        cv2.putText(overlay, str(index + 1), tuple(np.rint(center + [30, 10]).astype(int)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 255), 4, cv2.LINE_AA)
    cv2.imwrite(str(args.output / "patch_sampling_overlay.jpg"), overlay, [cv2.IMWRITE_JPEG_QUALITY, 95])
    print(json.dumps(report["decoded_neutral_axis_patches_2_to_5"], indent=2))
    print(json.dumps(report["decoded_linearity_fit_patches_2_to_5"], indent=2))


if __name__ == "__main__":
    main()
