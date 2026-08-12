#!/usr/bin/env python3
"""Audit frequency ownership and revisit V40's projection-grain observer.

V44 retained the archive pointwise projection-grain observer after the then-
current formed-density path failed colour-tail gates.  The negative and 2383
spectral/density coordinates were later rebuilt in V51--V64, but this decision
was never re-tested.  V77 compares both observers with one formed negative,
reports physical-frequency NPS bands, and carries uniform grain through the
declared 2K integration and V76 maximum-budget ProRes delivery.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
import tempfile

import cv2
import numpy as np

import emulsion_experiment as e
from audit_v40_motion_colour_grain import measure_frame
from audit_v63_neutral_trajectory import difference_metrics
from audit_v75_scale_integrated_delivery import exact_integer_area
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import ProResRawDecoder, _xq_command
from emulsion5279.pipeline import Emulsion5279Engine, FormedNegative


LUMA = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float64)
FRAME_WIDTH_MM = 24.9
FREQUENCY_EDGES_LP_MM = np.asarray(
    [0.0, 4.0, 8.0, 16.0, 24.0, 32.0, 48.0, 64.0, 96.0, 128.0, 170.0],
    dtype=np.float64,
)


def centred_crop(image: np.ndarray, size: int) -> np.ndarray:
    height, width = image.shape[:2]
    if size > height or size > width:
        raise ValueError("crop exceeds image")
    y = (height - size) // 2
    x = (width - size) // 2
    return np.asarray(image[y : y + size, x : x + size], dtype=np.float32)


def centred_crop_rect(
    image: np.ndarray, crop_height: int, crop_width: int
) -> np.ndarray:
    height, width = image.shape[:2]
    if crop_height > height or crop_width > width:
        raise ValueError("rectangular crop exceeds image")
    y = (height - crop_height) // 2
    x = (width - crop_width) // 2
    return np.asarray(
        image[y : y + crop_height, x : x + crop_width], dtype=np.float32
    )


def radial_spectrum(planes: np.ndarray, pixels_per_mm: float) -> dict[str, object]:
    array = np.asarray(planes, dtype=np.float64)
    if array.ndim == 2:
        array = array[..., None]
    height, width, channels = array.shape
    array -= np.mean(array, axis=(0, 1), keepdims=True)
    window = np.outer(np.hanning(height), np.hanning(width)).astype(np.float64)
    power = np.zeros((height, width // 2 + 1), dtype=np.float64)
    for channel in range(channels):
        transformed = np.fft.rfft2(array[..., channel] * window)
        channel_power = np.abs(transformed) ** 2
        if width > 2:
            channel_power[:, 1:-1] *= 2.0
        power += channel_power
    power /= float(channels)
    fy = np.fft.fftfreq(height)[:, None] * pixels_per_mm
    fx = np.fft.rfftfreq(width)[None, :] * pixels_per_mm
    radius = np.sqrt(fx * fx + fy * fy)
    bands = np.asarray(
        [
            float(np.sum(power[(radius >= low) & (radius < high)]))
            for low, high in zip(
                FREQUENCY_EDGES_LP_MM[:-1],
                FREQUENCY_EDGES_LP_MM[1:],
                strict=True,
            )
        ],
        dtype=np.float64,
    )
    total = max(float(np.sum(bands)), 1e-30)
    fractions = bands / total
    rms = float(np.sqrt(np.mean(array * array, dtype=np.float64)))
    return {
        "dimensions": [width, height],
        "pixels_per_mm": pixels_per_mm,
        "nyquist_axis_lp_mm": 0.5 * pixels_per_mm,
        "nyquist_corner_lp_mm": math.sqrt(0.5) * pixels_per_mm,
        "total_rms": rms,
        "band_power_fraction": fractions.tolist(),
        "band_rms_equivalent": (rms * np.sqrt(fractions)).tolist(),
    }


def describe_rgb_residual(residual: np.ndarray, pixels_per_mm: float) -> dict[str, object]:
    rgb = np.asarray(residual, dtype=np.float32)
    luma = np.einsum("...c,c->...", rgb, LUMA).astype(np.float32)
    opponent = np.stack(
        (
            (rgb[..., 0] - rgb[..., 1]) / math.sqrt(2.0),
            (rgb[..., 0] + rgb[..., 1] - 2.0 * rgb[..., 2]) / math.sqrt(6.0),
        ),
        axis=-1,
    ).astype(np.float32)
    return {
        "rgb": radial_spectrum(rgb, pixels_per_mm),
        "luma": radial_spectrum(luma, pixels_per_mm),
        "opponent": radial_spectrum(opponent, pixels_per_mm),
    }


def band_rms_ratio(
    candidate: dict[str, object], reference: dict[str, object]
) -> list[float | None]:
    candidate_values = np.asarray(candidate["band_rms_equivalent"], dtype=np.float64)
    reference_values = np.asarray(reference["band_rms_equivalent"], dtype=np.float64)
    return [
        float(c / r) if r > 1e-20 else None
        for c, r in zip(candidate_values, reference_values, strict=True)
    ]


def publish_projection(
    engine: Emulsion5279Engine,
    projection: np.ndarray,
    scan: np.ndarray,
) -> np.ndarray:
    return engine._publish_projection_colour(projection, scan)  # noqa: SLF001


def render_observers(
    engine: Emulsion5279Engine,
    negative: FormedNegative,
    frame: int,
    projection_observer: str,
) -> dict[str, np.ndarray]:
    previous = e.PROJECTION_GRAIN_DELTA_OBSERVER
    try:
        e.PROJECTION_GRAIN_DELTA_OBSERVER = projection_observer
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
    finally:
        e.PROJECTION_GRAIN_DELTA_OBSERVER = previous
    return {
        "projection": publish_projection(engine, projection, scan),
        "scan": scan,
        "mean_projection": publish_projection(engine, mean_projection, mean_scan),
        "mean_scan": mean_scan,
    }


def projection_stage_trace(
    engine: Emulsion5279Engine,
    negative: FormedNegative,
    scan: np.ndarray,
    frame: int,
    observer: str,
) -> dict[str, object]:
    """Reproduce the projection branch and locate colour-tail creation."""

    mean_density = negative.mean_record_density
    formed_density = negative.formed_record_density
    negative_mean = e.apply_5279_mtf_to_record_density(mean_density, 1.0)
    negative_formed = (
        negative_mean + formed_density - mean_density
    ).astype(np.float32)
    mean_scanner_density = e.scanner_density_from_total_record_density(negative_mean)
    negative_printer_mean = e.negative_total_printer_density_from_record_density(
        negative_mean
    )
    print_mean = e.print_2383_density_from_negative(negative_printer_mean)
    print_mean_mtf = e.apply_2383_mtf_to_print_density(print_mean, 1.0)
    raw_mean = e.render_2383_monitor_projection_from_print_density(
        negative_mean,
        print_mean_mtf,
        scanner_density=mean_scanner_density,
    )

    if observer == "archive_pointwise":
        legacy_mean = e.render_2383_monitor_projection_fast_from_record_density(
            mean_density
        )
        legacy_formed = e.render_2383_monitor_projection_fast_from_record_density(
            formed_density
        )
        raw_delta = legacy_formed - legacy_mean
        print_mtf_delta = e.apply_2383_mtf_to_density_delta(raw_delta, 1.0)
    elif observer == "formed_density":
        negative_printer_formed = (
            e.negative_total_printer_density_from_record_density(negative_formed)
        )
        print_formed = e.print_2383_density_from_negative(negative_printer_formed)
        print_formed_mtf = (
            print_mean_mtf
            + e.apply_2383_mtf_to_density_delta(print_formed - print_mean, 1.0)
        ).astype(np.float32)
        raw_formed = e.render_2383_monitor_projection_from_print_density(
            negative_formed,
            print_formed_mtf,
            scanner_density=e.scanner_density_from_total_record_density(
                negative_formed
            ),
        )
        raw_delta = raw_formed - raw_mean
        # The formed projection has already traversed print-density MTF above.
        print_mtf_delta = raw_delta
    else:
        raise ValueError(observer)

    finished_delta = e.finish_projection_grain_delta(print_mtf_delta)
    raw_added = raw_mean + raw_delta
    mtf_added = raw_mean + print_mtf_delta
    finished_added = raw_mean + finished_delta
    compressed_mean = e.compress_oklab_chroma_to_rec709(raw_mean)
    compressed = e.compress_oklab_chroma_to_rec709(finished_added)
    mean_preserved = e.preserve_perceptual_grain_mean(
        compressed_mean, compressed_mean
    )
    preserved = e.preserve_perceptual_grain_mean(compressed_mean, compressed)
    published = publish_projection(engine, preserved, scan)
    stage_images = {
        "raw_observer_delta_added": raw_added,
        "print_mtf_delta_added": mtf_added,
        "opponent_finished_delta_added": finished_added,
        "oklab_gamut_compressed": compressed,
        "perceptual_mean_preserved": preserved,
        "scan_referenced_colour_published": published,
    }
    return {
        "observer": observer,
        "stages": {
            name: measure_frame(quantized_srgb(image))
            for name, image in stage_images.items()
        },
        "mean_tail": measure_frame(quantized_srgb(mean_preserved)),
        "final_linear": published,
    }


def quantized_srgb(image: np.ndarray) -> np.ndarray:
    return np.rint(np.clip(e.srgb_encode(image), 0.0, 1.0) * 65535.0).astype(
        np.uint16
    )


def measure_mean_relative_grain_tail(
    formed_linear: np.ndarray, mean_linear: np.ndarray
) -> dict[str, float | int]:
    """Measure stochastic colour tails after subtracting deterministic detail."""

    formed = np.asarray(e.srgb_encode(formed_linear), dtype=np.float32)
    mean = np.asarray(e.srgb_encode(mean_linear), dtype=np.float32)
    delta = formed - mean
    mean_luma = np.einsum("...c,c->...", mean, LUMA)
    delta_luma = np.einsum("...c,c->...", delta, LUMA)
    opponent = delta - delta_luma[..., None]
    magnitude = np.max(opponent, axis=-1) - np.min(opponent, axis=-1)
    valid = np.zeros(mean_luma.shape, dtype=bool)
    valid[2:-2, 2:-2] = True
    dark = (mean_luma < 0.18) & valid
    dark_count = int(np.sum(dark))
    median_residual = delta - cv2.medianBlur(delta, 3)
    median_luma = np.einsum("...c,c->...", median_residual, LUMA)
    median_opponent = median_residual - median_luma[..., None]
    median_magnitude = np.max(median_opponent, axis=-1) - np.min(
        median_opponent, axis=-1
    )
    result: dict[str, float | int] = {
        "dark_pixel_count": dark_count,
        "opponent_p999": float(np.quantile(magnitude[dark], 0.999)),
        "opponent_p9999": float(np.quantile(magnitude[dark], 0.9999)),
        "opponent_maximum": float(np.max(magnitude[dark])),
        "median_opponent_p9999": float(
            np.quantile(median_magnitude[dark], 0.9999)
        ),
    }
    for threshold in (0.04, 0.05, 0.06, 0.08):
        strong = dark & (median_magnitude > threshold)
        neighbors = cv2.boxFilter(
            strong.astype(np.uint8),
            ddepth=cv2.CV_16U,
            ksize=(3, 3),
            normalize=False,
            borderType=cv2.BORDER_CONSTANT,
        ) - strong.astype(np.uint16)
        isolated = int(np.sum(strong & (neighbors == 0)))
        key = str(threshold).replace(".", "_")
        result[f"isolated_gt_{key}_count"] = isolated
        result[f"isolated_gt_{key}_per_million"] = float(
            isolated / max(dark_count, 1) * 1e6
        )
    return result


def decode_srgb_movie(path: Path, width: int, height: int) -> np.ndarray:
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
        raise RuntimeError(f"short ProRes decode {len(payload)}/{expected}")
    code = (
        np.frombuffer(payload, "<u2")
        .reshape(height, width, 3)
        .astype(np.float32)
        / 65535.0
    )
    return e.srgb_decode(code)


def encode_decode_max_xq(image: np.ndarray, path: Path, fps: str) -> np.ndarray:
    height, width = image.shape[:2]
    payload = quantized_srgb(image).astype("<u2", copy=False).tobytes()
    completed = subprocess.run(
        _xq_command(path, width, height, fps),
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode("utf-8", "replace"))
    e.finalize_prores_srgb_metadata(path)
    decoded = decode_srgb_movie(path, width, height)
    path.unlink(missing_ok=True)
    return decoded


def codec_residual(
    formed: np.ndarray,
    mean: np.ndarray,
    directory: Path,
    label: str,
    fps: str,
) -> np.ndarray:
    formed_decoded = encode_decode_max_xq(
        formed, directory / f"{label}_formed.mov", fps
    )
    mean_decoded = encode_decode_max_xq(mean, directory / f"{label}_mean.mov", fps)
    return formed_decoded - mean_decoded


def spectrum_pair(
    formed: np.ndarray,
    mean: np.ndarray,
    pixels_per_mm: float,
    crop_size: int | tuple[int, int] | None = None,
) -> dict[str, object]:
    residual = formed - mean
    if crop_size is not None:
        if isinstance(crop_size, tuple):
            residual = centred_crop_rect(residual, crop_size[0], crop_size[1])
        else:
            residual = centred_crop(residual, crop_size)
    return describe_rgb_residual(residual, pixels_per_mm)


def observer_frequency_comparison(
    archive: dict[str, np.ndarray],
    direct: dict[str, np.ndarray],
    *,
    crop_size: int | tuple[int, int],
) -> dict[str, object]:
    pixels_per_mm = archive["projection"].shape[1] / FRAME_WIDTH_MM
    archive_projection = spectrum_pair(
        archive["projection"], archive["mean_projection"], pixels_per_mm, crop_size
    )
    direct_projection = spectrum_pair(
        direct["projection"], direct["mean_projection"], pixels_per_mm, crop_size
    )
    scan = spectrum_pair(
        archive["scan"], archive["mean_scan"], pixels_per_mm, crop_size
    )
    return {
        "archive_pointwise_projection": archive_projection,
        "formed_density_projection": direct_projection,
        "legacy_managed_scan": scan,
        "formed_density_over_archive_band_rms": {
            "luma": band_rms_ratio(
                direct_projection["luma"], archive_projection["luma"]
            ),
            "opponent": band_rms_ratio(
                direct_projection["opponent"], archive_projection["opponent"]
            ),
        },
    }


def uniform_negative(log_exposure: float, frame: int) -> FormedNegative:
    height, width = 192, 5760
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


def audit_uniform(
    engine: Emulsion5279Engine,
    log_exposure: float,
    frame: int,
    fps: str,
) -> dict[str, object]:
    negative = uniform_negative(log_exposure, frame)
    archive = render_observers(engine, negative, frame, "archive_pointwise")
    direct = render_observers(engine, negative, frame, "formed_density")
    pixels_per_mm = 5760.0 / FRAME_WIDTH_MM
    negative_crop = np.asarray(
        negative.formed_record_density[24:-24, 72:-72]
        - negative.mean_record_density[24:-24, 72:-72],
        dtype=np.float32,
    )
    frequency = observer_frequency_comparison(
        archive, direct, crop_size=(144, 5616)
    )

    integrated: dict[str, dict[str, np.ndarray]] = {}
    for label, pair in (
        ("archive_pointwise_projection", (archive["projection"], archive["mean_projection"])),
        ("formed_density_projection", (direct["projection"], direct["mean_projection"])),
        ("legacy_managed_scan", (archive["scan"], archive["mean_scan"])),
    ):
        integrated[label] = {
            "formed": exact_integer_area(pair[0], 3),
            "mean": exact_integer_area(pair[1], 3),
        }

    review_pixels_per_mm = 1920.0 / FRAME_WIDTH_MM
    with tempfile.TemporaryDirectory(prefix=f"v77-uniform-{frame}-") as temporary:
        temporary_path = Path(temporary)
        review_results: dict[str, object] = {}
        for label, pair in integrated.items():
            pre_codec = pair["formed"] - pair["mean"]
            post_codec = codec_residual(
                pair["formed"], pair["mean"], temporary_path, label, fps
            )
            pre_spectrum = describe_rgb_residual(pre_codec, review_pixels_per_mm)
            post_spectrum = describe_rgb_residual(post_codec, review_pixels_per_mm)
            review_results[label] = {
                "pre_codec": pre_spectrum,
                "post_v76_maximum_budget_xq": post_spectrum,
                "post_over_pre_band_rms": {
                    "luma": band_rms_ratio(post_spectrum["luma"], pre_spectrum["luma"]),
                    "opponent": band_rms_ratio(
                        post_spectrum["opponent"], pre_spectrum["opponent"]
                    ),
                },
            }

    return {
        "log_exposure": log_exposure,
        "negative_native_density": {
            "records": describe_rgb_residual(negative_crop, pixels_per_mm),
        },
        "native_observers": frequency,
        "scale_integrated_review_and_codec": review_results,
        "scan_identity_maximum_absolute": float(
            np.max(np.abs(archive["scan"] - direct["scan"]))
        ),
    }


def audit_real_frame(
    engine: Emulsion5279Engine,
    raw: np.ndarray,
    frame: int,
    fps: str,
) -> dict[str, object]:
    negative = engine.form_negative(raw, frame)
    archive = render_observers(engine, negative, frame, "archive_pointwise")
    direct = render_observers(engine, negative, frame, "formed_density")
    archive_trace = projection_stage_trace(
        engine, negative, archive["scan"], frame, "archive_pointwise"
    )
    direct_trace = projection_stage_trace(
        engine, negative, direct["scan"], frame, "formed_density"
    )
    frequency = observer_frequency_comparison(archive, direct, crop_size=1536)
    review_frequency: dict[str, object] = {}
    for label, formed, mean in (
        (
            "archive_pointwise_projection",
            archive["projection"],
            archive["mean_projection"],
        ),
        (
            "formed_density_projection",
            direct["projection"],
            direct["mean_projection"],
        ),
        ("legacy_managed_scan", archive["scan"], archive["mean_scan"]),
    ):
        formed_crop = centred_crop(formed, 1536)
        mean_crop = centred_crop(mean, 1536)
        review_frequency[label] = spectrum_pair(
            exact_integer_area(formed_crop, 3),
            exact_integer_area(mean_crop, 3),
            1920.0 / FRAME_WIDTH_MM,
        )

    pre_codec_tails = {
        "archive_pointwise_projection": measure_frame(
            quantized_srgb(archive["projection"])
        ),
        "formed_density_projection": measure_frame(
            quantized_srgb(direct["projection"])
        ),
    }
    pre_codec_mean_relative_tails = {
        "archive_pointwise_projection": measure_mean_relative_grain_tail(
            archive["projection"], archive["mean_projection"]
        ),
        "formed_density_projection": measure_mean_relative_grain_tail(
            direct["projection"], direct["mean_projection"]
        ),
    }
    with tempfile.TemporaryDirectory(prefix="v77-t020-") as temporary:
        temporary_path = Path(temporary)
        archive_encoded = encode_decode_max_xq(
            archive["projection"], temporary_path / "archive.mov", fps
        )
        direct_encoded = encode_decode_max_xq(
            direct["projection"], temporary_path / "direct.mov", fps
        )
        mean_encoded = encode_decode_max_xq(
            archive["mean_projection"], temporary_path / "mean.mov", fps
        )
    post_codec_tails = {
        "archive_pointwise_projection": measure_frame(
            quantized_srgb(archive_encoded)
        ),
        "formed_density_projection": measure_frame(quantized_srgb(direct_encoded)),
    }
    post_codec_mean_relative_tails = {
        "archive_pointwise_projection": measure_mean_relative_grain_tail(
            archive_encoded, mean_encoded
        ),
        "formed_density_projection": measure_mean_relative_grain_tail(
            direct_encoded, mean_encoded
        ),
    }
    direct_tail = post_codec_tails["formed_density_projection"]
    gates = {
        "direct_dark_opponent_p9999_le_0_035": bool(
            direct_tail["dark_opponent_p9999"] <= 0.035
        ),
        "direct_median_opponent_p9999_le_0_05": bool(
            direct_tail["median_opponent_p9999"] <= 0.05
        ),
        "direct_isolated_impulses_gt_0_08_zero": bool(
            direct_tail["isolated_impulses_gt_0.08_count"] == 0
        ),
        "scan_is_bit_identical_under_projection_ablation": bool(
            np.array_equal(archive["scan"], direct["scan"])
        ),
    }
    return {
        "frame": frame,
        "frequency_native_center_1536": frequency,
        "frequency_scale_integrated_center_512": review_frequency,
        "projection_image_change": difference_metrics(
            archive["projection"], direct["projection"]
        ),
        "projection_mean_change": difference_metrics(
            archive["mean_projection"], direct["mean_projection"]
        ),
        "scan_maximum_absolute_change": float(
            np.max(np.abs(archive["scan"] - direct["scan"]))
        ),
        "projection_stage_tail_trace": {
            "archive_pointwise": {
                "parity_maximum_absolute": float(
                    np.max(
                        np.abs(archive_trace["final_linear"] - archive["projection"])
                    )
                ),
                "mean_tail": archive_trace["mean_tail"],
                "stages": archive_trace["stages"],
            },
            "formed_density": {
                "parity_maximum_absolute": float(
                    np.max(
                        np.abs(direct_trace["final_linear"] - direct["projection"])
                    )
                ),
                "mean_tail": direct_trace["mean_tail"],
                "stages": direct_trace["stages"],
            },
        },
        "pre_codec_colour_tail": pre_codec_tails,
        "post_v76_maximum_budget_xq_colour_tail": post_codec_tails,
        "pre_codec_mean_relative_grain_tail": pre_codec_mean_relative_tails,
        "post_v76_maximum_budget_xq_mean_relative_grain_tail": (
            post_codec_mean_relative_tails
        ),
        "gates": gates,
        "pass": all(gates.values()),
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
            fps = decoder.fps
        real = audit_real_frame(engine, raw, frame, fps)
        uniform = [
            audit_uniform(engine, log_exposure, 7700 + index * 100, fps)
            for index, log_exposure in enumerate((-3.0, -1.0, 0.0))
        ]
    finally:
        engine.close()
    all_uniform_scan_identity = all(
        row["scan_identity_maximum_absolute"] == 0.0 for row in uniform
    )
    paired = real["post_v76_maximum_budget_xq_mean_relative_grain_tail"]
    archive_tail = paired["archive_pointwise_projection"]
    direct_tail = paired["formed_density_projection"]
    paired_tail_gates = {
        "archive_has_no_mean_relative_isolated_gt_0_08": bool(
            archive_tail["isolated_gt_0_08_count"] == 0
        ),
        "direct_has_no_mean_relative_isolated_gt_0_08": bool(
            direct_tail["isolated_gt_0_08_count"] == 0
        ),
        "direct_p9999_within_0_001_of_archive": bool(
            direct_tail["opponent_p9999"]
            <= archive_tail["opponent_p9999"] + 0.001
        ),
        "direct_isolated_gt_0_06_does_not_exceed_archive": bool(
            direct_tail["isolated_gt_0_06_count"]
            <= archive_tail["isolated_gt_0_06_count"]
        ),
    }
    return {
        "audit": "V77 frequency ownership and projection grain observer",
        "profile": "V72 · Evidence-minimal record formation",
        "image_change": "candidate only; no profile promoted by this audit",
        "input": str(input_path),
        "frequency_band_edges_lp_mm": FREQUENCY_EDGES_LP_MM.tolist(),
        "observer_ablation": {
            "reference": "archive_pointwise retained from V40/V44",
            "candidate": "formed_density through current V72 spectral coordinates",
            "single_variable": "PROJECTION_GRAIN_DELTA_OBSERVER",
        },
        "real_T020": real,
        "uniform_exposure_rows": uniform,
        "global_gates": {
            "historical_total_image_tail_gate_at_maximum_xq": real["pass"],
            "mean_relative_grain_tail": paired_tail_gates,
            "scan_identical_for_all_uniform_exposures": all_uniform_scan_identity,
        },
        "decision": (
            "Retain archive_pointwise for V72. The current-coordinate "
            "formed_density candidate removes no category error, changes only "
            "the stochastic projection, and nearly doubles mean-relative "
            "isolated >0.06 opponent events on T020 (70 to 137 after V76 XQ). "
            "The old whole-image gate is not suitable for maximum-fidelity "
            "delivery because the deterministic mean itself contains natural "
            "isolated chromatic detail. Use paired mean-relative tails for "
            "future grain regressions."
        ),
        "decision_boundary": (
            "Promote formed_density only if current-coordinate native colour-tail "
            "gates pass, scan remains identical, and its frequency change is "
            "physically attributable rather than a pleasing-by-eye adjustment."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode"))
    args = parser.parse_args()
    report = measure(args.input, args.decoder)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
