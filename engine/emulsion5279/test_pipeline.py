from __future__ import annotations

import concurrent.futures
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np
import cv2

from .contracts import (
    DeliveryEncoding,
    EngineConfig,
    EngineMode,
    ObserverPair,
    RenderedFrame,
)
from .conformance import research_conformance
from .io import (
    DualDeliveryWriter,
    PrefetchedIterator,
    rebuild_scale_integrated_srgb_review_from_master,
)
from .pipeline import Emulsion5279Engine
from . import legacy


class PipelineContractTests(unittest.TestCase):
    def test_config_rejects_creative_or_invalid_engine_controls(self) -> None:
        with self.assertRaises(ValueError):
            EngineConfig(profile="pretty-film")
        with self.assertRaises(ValueError):
            EngineConfig(oversample=0)
        with self.assertRaises(ValueError):
            EngineConfig(grain_scale=-1.0)
        with self.assertRaises(ValueError):
            EngineConfig(exposure_stops=0.0)
        with self.assertRaises(ValueError):
            EngineConfig(observer_branch_workers=3)
        experimental = EngineConfig(
            exposure_stops=0.0,
            research_baseline=False,
            mode=EngineMode.REFERENCE,
        )
        self.assertFalse(experimental.research_baseline)

    def test_bounded_prefetch_preserves_order_and_stops_at_count(self) -> None:
        values = [(index, index * index) for index in range(5)]
        for enabled in (False, True):
            with PrefetchedIterator(
                iter(values), enabled=enabled, count=3
            ) as prefetched:
                self.assertEqual(list(prefetched), [(0, 0), (1, 1), (2, 4)])
                self.assertGreaterEqual(prefetched.last_service_seconds, 0.0)
                self.assertGreaterEqual(prefetched.last_wait_seconds, 0.0)

    def test_default_executes_the_latest_research_sampler_contract(self) -> None:
        config = EngineConfig()
        self.assertEqual(config.mode, EngineMode.PRODUCTION_METAL)
        legacy.profile.apply(legacy.model)
        report = research_conformance(legacy.model, legacy.profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertTrue(report["production_execution_conformant"])
        self.assertTrue(all(report["checks"].values()))

    def test_v43h_is_isolated_and_v42_resets_every_hypothesis(self) -> None:
        import v43h_profile
        import v42_profile

        e = legacy.model
        config = EngineConfig(profile="v43h", mode=EngineMode.REFERENCE)
        v43h_profile.apply(e)
        report = research_conformance(e, v43h_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(e.PRINT_GRAIN_DOMAIN, "hypothesis_common_density")
        np.testing.assert_array_equal(
            e.SPIRIT_PERIOD_OBSERVER_CENTRES_NM,
            np.array([622.5, 542.5, 467.5], dtype=np.float32),
        )

        v42_profile.apply(e)
        self.assertEqual(e.PRINT_GRAIN_DOMAIN, "none")
        self.assertEqual(e.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE, 0.0)
        np.testing.assert_array_equal(
            e.SPIRIT_PERIOD_OBSERVER_CENTRES_NM,
            np.array([620.0, 540.0, 470.0], dtype=np.float32),
        )

    def test_v44_withholds_hypotheses_and_retains_accepted_colour_boundary(self) -> None:
        import v44_profile
        from apply_v31_normal_process_adapter import adapt_frame_linear

        e = legacy.model
        config = EngineConfig(profile="v44", mode=EngineMode.REFERENCE)
        v44_profile.apply(e)
        report = research_conformance(e, v44_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(e.PRINT_GRAIN_DOMAIN, "none")
        self.assertEqual(e.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE, 0.0)

        engine = Emulsion5279Engine(config)
        engine.profile = v44_profile
        rng = np.random.default_rng(44)
        projection = rng.uniform(0.02, 0.8, (16, 20, 3)).astype(np.float32)
        scan = rng.uniform(0.02, 0.8, (16, 20, 3)).astype(np.float32)
        published = engine._publish_projection_colour(projection, scan)
        expected = adapt_frame_linear(
            projection,
            scan,
            v44_profile.PROFILE[
                "final_adapter_opponent_high_frequency_retention"
            ],
        )
        np.testing.assert_array_equal(published, expected)

    def test_v43h_common_print_density_has_no_record_separation(self) -> None:
        import v43h_profile

        e = legacy.model
        v43h_profile.apply(e)
        density = np.full((48, 64, 3), 1.0, dtype=np.float32)
        formed = e.form_2383_hypothesis_common_grain_density(
            density, frame_index=12, grain_scale=1.0
        )
        delta = formed - density
        np.testing.assert_array_equal(delta[..., 0], delta[..., 1])
        np.testing.assert_array_equal(delta[..., 1], delta[..., 2])
        self.assertLess(abs(float(delta.mean())), 2e-4)

    def test_two_delivery_encodings_reconstruct_the_same_light(self) -> None:
        rng = np.random.default_rng(5279)
        projection = rng.uniform(0.0, 1.0, (12, 16, 3)).astype(np.float32)
        scan = rng.uniform(0.0, 1.0, (12, 16, 3)).astype(np.float32)
        master, quicktime = Emulsion5279Engine.encode(
            ObserverPair(projection, scan)
        )
        self.assertEqual(master.encoding, DeliveryEncoding.REFERENCE_BT1886)
        self.assertEqual(quicktime.encoding, DeliveryEncoding.QUICKTIME_SRGB)
        np.testing.assert_allclose(
            legacy.model.bt1886_reference_decode(master.projection),
            projection,
            rtol=2e-6,
            atol=2e-7,
        )
        np.testing.assert_allclose(
            legacy.model.srgb_decode(quicktime.scan),
            scan,
            rtol=2e-6,
            atol=2e-7,
        )

    def test_disabled_d60_authority_neither_loads_nor_changes_pixels(self) -> None:
        e = legacy.model
        legacy.profile.apply(e)
        self.assertEqual(e.PRINT_2383_D60_RELATIVE_CHROMA_STRENGTH, 0.0)
        rng = np.random.default_rng(41)
        density = rng.uniform(0.0, 2.0, (10, 12, 3)).astype(np.float32)
        monitor = rng.uniform(-0.02, 1.02, (10, 12, 3)).astype(np.float32)
        expected = np.clip(
            e.compress_oklab_chroma_to_rec709(
                e.oklab_to_linear_rec709(e.linear_rec709_to_oklab(monitor))
            ),
            0.0,
            1.0,
        ).astype(np.float32)
        original = e.PRINT_2383_D60_RELATIVE_CHROMA_DELTA_PATH
        with tempfile.TemporaryDirectory() as directory:
            e.PRINT_2383_D60_RELATIVE_CHROMA_DELTA_PATH = (
                Path(directory) / "deliberately-absent.npz"
            )
            actual = e.apply_2383_d60_relative_chroma_calibration(density, monitor)
        e.PRINT_2383_D60_RELATIVE_CHROMA_DELTA_PATH = original
        np.testing.assert_array_equal(actual, expected)

    def test_shared_projection_scan_metrics_are_bit_exact(self) -> None:
        """Sharing scan-side 2383 metrics cannot change the colour match."""
        e = legacy.model
        legacy.profile.apply(e)
        rng = np.random.default_rng(238343)
        physical = rng.uniform(0.0, 1.0, (72, 96, 3)).astype(np.float32)
        scan = rng.uniform(0.0, 1.0, physical.shape).astype(np.float32)
        expected = e.match_2383_projection_to_rec709_monitor(physical, scan)
        metrics = e.projection_monitor_scan_metrics(scan)
        actual = e.match_2383_projection_to_rec709_monitor(
            physical, scan, scan_metrics=metrics
        )
        np.testing.assert_array_equal(actual, expected)

    def test_parallel_observers_are_bit_exact(self) -> None:
        """Scheduling the two independent observers cannot alter their math."""
        import v43h_profile

        e = legacy.model
        v43h_profile.apply(e)
        rng = np.random.default_rng(4309)
        mean = rng.uniform(0.1, 2.0, (36, 48, 3)).astype(np.float32)
        formed = (mean + rng.normal(0.0, 0.02, mean.shape)).astype(np.float32)
        sequential = e.reconstruct_density_pair_to_dual_display_v39(
            mean,
            formed,
            17,
            1.0,
            "linear_rec709",
            return_mean_pair=True,
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            parallel = e.reconstruct_density_pair_to_dual_display_v39(
                mean,
                formed,
                17,
                1.0,
                "linear_rec709",
                return_mean_pair=True,
                branch_executor=executor,
            )
        for expected, actual in zip(sequential, parallel, strict=True):
            np.testing.assert_array_equal(actual, expected)

    def test_zero_projection_hf_residual_shortcut_is_bit_exact(self) -> None:
        """V40+'s zero-retention branch preserves the historical equation."""
        e = legacy.model
        legacy.profile.apply(e)
        self.assertEqual(e.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION, 0.0)
        rng = np.random.default_rng(4043)
        delta = rng.normal(0.0, 0.01, (72, 96, 3)).astype(np.float32)
        luma = np.einsum(
            "...c,c->...", delta, [0.2126, 0.7152, 0.0722]
        )
        common = luma[..., None]
        opponent = delta - common
        sigma = max(
            e.PROJECTION_CHROMA_GRAIN_SIGMA_AT_2K * delta.shape[1] / 2048.0,
            0.05,
        )
        opponent_low = cv2.GaussianBlur(
            opponent, (0, 0), sigma, borderType=cv2.BORDER_REFLECT
        )
        historical = (
            common
            + (
                opponent_low
                + e.PROJECTION_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION
                * (opponent - opponent_low)
            )
            * e.PROJECTION_CHROMA_GRAIN_OPPONENT_STRENGTH
        ).astype(np.float32)
        optimized = e.finish_projection_grain_delta(delta)
        np.testing.assert_array_equal(optimized, historical)

    def test_deterministic_grain_mean_shortcut_is_bit_exact(self) -> None:
        """The no-grain observer must retain the historical float32 result."""
        e = legacy.model
        rng = np.random.default_rng(43)
        reference = rng.uniform(-0.04, 1.04, (72, 96, 3)).astype(np.float32)
        historical = e.preserve_perceptual_grain_mean(
            reference, reference.copy()
        )
        optimized = e.preserve_perceptual_grain_mean(reference, reference)
        np.testing.assert_array_equal(optimized, historical)

    def test_fused_h61_sampler_is_bit_exact(self) -> None:
        """The Production sampler preserves H-61's original operation order."""
        import pipeline_accel

        e = legacy.model
        legacy.profile.apply(e)
        rng = np.random.default_rng(61)
        density = (
            e.SENSITO_DMIN_RGB
            + rng.uniform(-0.12, 3.0, (72, 96, 3)).astype(np.float32)
        )
        expected = e.apply_2383_h61_colour_delta_lut(density, True)
        lut = e._PRINT_2383_H61_COLOUR_DELTA_LUTS[True]
        actual = pipeline_accel.h61_density_cube_trilinear(
            density,
            lut,
            e.SENSITO_DMIN_RGB,
            -0.16,
            e.NEGATIVE_5279_MAX_RECORD_DENSITY,
        )
        np.testing.assert_array_equal(actual, expected)

    def test_fused_2383_projection_sampler_is_bit_exact(self) -> None:
        """Spectral 2383 LUT fusion cannot alter projected RGB samples."""
        import pipeline_accel

        e = legacy.model
        legacy.profile.apply(e)
        rng = np.random.default_rng(2383)
        density = rng.uniform(
            -0.10, e.PRINT_2383_DMAX + 0.10, (72, 96, 3)
        ).astype(np.float32)
        expected = e.apply_2383_projection_lut(density)
        actual = pipeline_accel.density_cube_trilinear(
            density,
            e._PRINT_2383_PROJECTION_LUT,
            e.PRINT_2383_DMAX,
        )
        np.testing.assert_array_equal(actual, expected)

    def test_fused_5279_printer_sampler_is_bit_exact(self) -> None:
        """Fusing spectral negative-to-print sampling preserves every value."""
        import pipeline_accel

        e = legacy.model
        legacy.profile.apply(e)
        rng = np.random.default_rng(52792383)
        density = rng.uniform(
            -0.10,
            e.NEGATIVE_5279_MAX_RECORD_DENSITY + 0.10,
            (72, 96, 3),
        ).astype(np.float32)
        expected = e.apply_5279_to_2383_printer_density_lut(density)
        actual = pipeline_accel.density_cube_trilinear(
            density,
            e._NEGATIVE_5279_TO_2383_PRINTER_DENSITY_LUT,
            e.NEGATIVE_5279_MAX_RECORD_DENSITY,
        )
        np.testing.assert_array_equal(actual, expected)

    def test_fused_channel_curve_interpolation_is_bit_exact(self) -> None:
        """Parallel 2383 H-D interpolation retains NumPy's float32 result."""
        import pipeline_accel

        rng = np.random.default_rng(238361)
        axis = np.linspace(-4.0, 1.0, 41, dtype=np.float32)
        tables = np.stack(
            [
                np.linspace(0.03, 3.8, 41, dtype=np.float32),
                np.linspace(0.04, 3.7, 41, dtype=np.float32) ** 1.01,
                np.linspace(0.02, 3.6, 41, dtype=np.float32) ** 0.99,
            ]
        ).astype(np.float32)
        values = rng.uniform(-4.5, 1.5, (72, 96, 3)).astype(np.float32)
        expected = np.empty_like(values)
        for channel in range(3):
            expected[..., channel] = np.interp(
                values[..., channel], axis, tables[channel]
            ).astype(np.float32)
        actual = pipeline_accel.channel_table_interp(values, axis, tables)
        np.testing.assert_array_equal(actual, expected)

    def test_fused_v31_gamut_boundary_is_bit_exact(self) -> None:
        """The faster normal-process boundary preserves every float32 sample."""
        import apply_v31_normal_process_adapter as adapter
        import pipeline_accel

        rng = np.random.default_rng(31)
        rgb = rng.uniform(-0.20, 1.20, (72, 96, 3)).astype(np.float32)
        target = rng.uniform(0.0, 1.0, (72, 96)).astype(np.float32)
        expected = adapter.preserve_luma_and_compress_gamut(rgb, target)
        actual = pipeline_accel.preserve_luma_and_compress_gamut(rgb, target)
        np.testing.assert_array_equal(actual, expected)

    def test_zero_retention_v31_shortcut_is_bit_exact(self) -> None:
        """With withdrawn HF authority, the skipped projection blur is zero."""
        import apply_v31_normal_process_adapter as adapter
        import v31_profile

        e = legacy.model
        rng = np.random.default_rng(3100)
        projection = rng.uniform(0.0, 1.0, (72, 96, 3)).astype(np.float32)
        scan = rng.uniform(0.0, 1.0, projection.shape).astype(np.float32)
        projection_lab = e.linear_rec709_to_oklab(projection)
        scan_lab = e.linear_rec709_to_oklab(scan)
        sigma = max(
            float(
                v31_profile.PROFILE[
                    "projection_chroma_crossover_sigma_at_2k"
                ]
            )
            * projection.shape[1]
            / 2048.0,
            0.05,
        )
        projection_low_ab = cv2.GaussianBlur(
            projection_lab[..., 1:3],
            (0, 0),
            sigma,
            borderType=cv2.BORDER_REFLECT,
        )
        scan_low_ab = cv2.GaussianBlur(
            scan_lab[..., 1:3],
            (0, 0),
            sigma,
            borderType=cv2.BORDER_REFLECT,
        )
        historical_lab = projection_lab.copy()
        historical_lab[..., 1:3] = scan_low_ab + 0.0 * (
            projection_lab[..., 1:3] - projection_low_ab
        )
        historical_rgb = e.oklab_to_linear_rec709(historical_lab)
        projection_luma = np.einsum(
            "...c,c->...", projection, [0.2126, 0.7152, 0.0722]
        ).astype(np.float32)
        expected = adapter.preserve_luma_and_compress_gamut(
            historical_rgb, projection_luma
        )
        actual = adapter.adapt_frame_linear(projection, scan, 0.0)
        np.testing.assert_array_equal(actual, expected)

    def test_common_density_scalar_debias_is_bit_exact(self) -> None:
        """A common print event need not duplicate and discard two records."""
        e = legacy.model
        rng = np.random.default_rng(1383)
        level = rng.uniform(0.0, 1.0, (257, 389)).astype(np.float32)
        delta = rng.normal(0.0, 0.01, level.shape).astype(np.float32)
        expected = e.remove_tonal_grain_bias(
            np.repeat(level[..., None], 3, axis=-1),
            np.repeat(delta[..., None], 3, axis=-1),
        )[..., 0]
        actual = e.remove_tonal_grain_bias_scalar(level, delta)
        np.testing.assert_array_equal(actual, expected)

    def test_common_density_effective_delta_is_bit_exact(self) -> None:
        """The scalar observer path preserves three-record float32 rounding."""
        import v43h_profile

        e = legacy.model
        v43h_profile.apply(e)
        rng = np.random.default_rng(138343)
        density = rng.uniform(0.03, 3.8, (257, 389, 3)).astype(np.float32)
        formed = e.form_2383_hypothesis_common_grain_density(
            density, frame_index=12, grain_scale=1.0
        )
        expected = np.mean(formed - density, axis=-1).astype(np.float32)
        actual = e.form_2383_hypothesis_effective_common_grain_delta(
            density, frame_index=12, grain_scale=1.0
        )
        np.testing.assert_array_equal(actual, expected)

    def test_reference_mode_accepts_extended_linear_highlights(self) -> None:
        engine = Emulsion5279Engine(EngineConfig(mode=EngineMode.REFERENCE))
        raw = np.asarray([[[0.2, 1.4, 8.0]]], dtype=np.float32)
        np.testing.assert_array_equal(engine._validate_raw_frame(raw), raw)

    def test_release_companion_and_still_derive_from_encoded_master(self) -> None:
        width, height, frames = 64, 48, 2
        yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
        xx /= width - 1
        yy /= height - 1
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with DualDeliveryWriter(root, width, height, "24/1", frames) as writer:
                for frame_index in range(frames):
                    phase = frame_index * 0.01
                    observers = ObserverPair(
                        np.stack(
                            [
                                0.05 + 0.75 * xx,
                                0.08 + 0.70 * yy,
                                0.06 + 0.65 * (0.6 * xx + 0.4 * yy),
                            ],
                            axis=2,
                        ).astype(np.float32)
                        + phase,
                        np.stack(
                            [
                                0.07 + 0.65 * yy,
                                0.06 + 0.68 * xx,
                                0.09 + 0.60 * (0.4 * xx + 0.6 * yy),
                            ],
                            axis=2,
                        ).astype(np.float32)
                        + phase,
                    )
                    writer.write(
                        RenderedFrame(
                            frame_index,
                            observers,
                            Emulsion5279Engine.encode_reference(observers),
                        )
                    )
            for branch in ("projection", "bluray_scan"):
                branch_root = root / branch
                master = branch_root / "05_emulsion_master_prores4444.mov"
                companion = branch_root / "06_quicktime_preview_srgb_prores4444.mov"
                still = branch_root / "still_emulsion.jpg"
                self.assertTrue(master.exists() and companion.exists() and still.exists())
                metadata = json.loads(
                    subprocess.check_output(
                        [
                            "ffprobe",
                            "-v",
                            "error",
                            "-select_streams",
                            "v:0",
                            "-show_entries",
                            "stream=pix_fmt,profile,color_transfer,nb_frames",
                            "-of",
                            "json",
                            str(companion),
                        ],
                        text=True,
                    )
                )["streams"][0]
                self.assertEqual(metadata["profile"], "XQ")
                self.assertEqual(metadata["pix_fmt"], "yuv444p12le")
                self.assertEqual(metadata["color_transfer"], "iec61966-2-1")
                self.assertEqual(int(metadata["nb_frames"]), frames)

                def decode(path: Path) -> np.ndarray:
                    payload = subprocess.check_output(
                        [
                            "ffmpeg",
                            "-v",
                            "error",
                            "-i",
                            str(path),
                            "-vf",
                            (
                                "setparams=range=tv:color_primaries=bt709:"
                                "color_trc=bt709:colorspace=bt709"
                            ),
                            "-pix_fmt",
                            "rgb48le",
                            "-f",
                            "rawvideo",
                            "-",
                        ]
                    )
                    return (
                        np.frombuffer(payload, "<u2")
                        .reshape(frames, height, width, 3)
                        .astype(np.float32)
                        / 65535.0
                    )

                master_code = decode(master)
                companion_code = decode(companion)
                np.testing.assert_allclose(
                    legacy.model.bt1886_reference_decode(master_code),
                    legacy.model.srgb_decode(companion_code),
                    rtol=0.0,
                    atol=0.004,
                )
                still_rgb = cv2.cvtColor(
                    cv2.imread(str(still), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB
                ).astype(np.float32) / 255.0
                self.assertLess(
                    float(np.mean(np.abs(still_rgb - companion_code[frames // 2]))),
                    0.02,
                )
            review = root / "projection" / "07_scale_integrated_review.mov"
            report = rebuild_scale_integrated_srgb_review_from_master(
                root / "projection" / "05_emulsion_master_prores4444.mov",
                review,
                frames,
                32,
            )
            self.assertEqual(report["source_dimensions"], [width, height])
            self.assertEqual(report["review_dimensions"], [32, 24])
            review_probe = json.loads(
                subprocess.check_output(
                    [
                        "ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,pix_fmt,color_transfer",
                        "-of", "json", str(review),
                    ],
                    text=True,
                )
            )["streams"][0]
            self.assertEqual(review_probe["width"], 32)
            self.assertEqual(review_probe["height"], 24)
            self.assertEqual(review_probe["pix_fmt"], "yuv444p12le")
            self.assertEqual(review_probe["color_transfer"], "iec61966-2-1")


if __name__ == "__main__":
    unittest.main()
