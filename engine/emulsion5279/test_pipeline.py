from __future__ import annotations

import concurrent.futures
import json
import struct
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
    CineonDPXSequenceWriter,
    DualDeliveryWriter,
    PrefetchedIterator,
    _xq_command,
    rebuild_scale_integrated_srgb_review_from_master,
)
from .pipeline import Emulsion5279Engine
from .view_policy import (
    CineonViewPolicy,
    LEGACY_MANAGED_PROJECTION_CONTRACT,
    LEGACY_MANAGED_SCAN_CONTRACT,
    POLICY_CONTRACTS,
    render_cineon_view,
)
from . import legacy


class PipelineContractTests(unittest.TestCase):
    def test_projection_delivery_declares_historical_management_boundary(self) -> None:
        contract = LEGACY_MANAGED_PROJECTION_CONTRACT
        self.assertFalse(contract["pure_function_of_projected_print"])
        self.assertIn(
            "not_measured_5279_or_2383_property",
            contract["classification"],
        )
        engine = Emulsion5279Engine(
            EngineConfig(profile="v72", mode=EngineMode.REFERENCE)
        )
        try:
            provenance = engine.provenance
        finally:
            engine.close()
        self.assertEqual(
            provenance["legacy_projection_delivery_contract"], contract
        )

    def test_xq_delivery_uses_measured_maximum_macroblock_budget(self) -> None:
        command = _xq_command(Path("review.mov"), 1920, 1440, "24000/1001")
        self.assertEqual(command[command.index("-profile:v") + 1], "5")
        self.assertEqual(command[command.index("-bits_per_mb") + 1], "8192")

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

    def test_cineon_dpx_is_code_exact_and_declares_printing_density(self) -> None:
        width, height = 6, 4
        index = np.arange(width * height, dtype=np.uint16).reshape(
            height, width
        )
        expected = np.stack(
            [
                (index * 41) % 1024,
                (123 + index * 67) % 1024,
                (1023 - index * 29) % 1024,
            ],
            axis=-1,
        ).astype(np.uint16)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            writer = CineonDPXSequenceWriter(
                root, width, height, "24/1", 1, start_frame=17
            )
            writer.write(expected)
            writer.close()
            path = root / "00000017.dpx"
            header = path.read_bytes()[:1664]
            endian = ">" if header[:4] == b"SDPX" else "<"
            self.assertEqual(struct.unpack_from(endian + "I", header, 784)[0], 0)
            self.assertEqual(struct.unpack_from(endian + "f", header, 788)[0], 0.0)
            self.assertEqual(struct.unpack_from(endian + "I", header, 792)[0], 1023)
            self.assertAlmostEqual(
                struct.unpack_from(endian + "f", header, 796)[0], 2.048,
                places=6,
            )
            self.assertEqual(header[800:804], bytes((50, 1, 1, 10)))
            decoded = subprocess.check_output(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-pix_fmt",
                    "gbrp10le",
                    "-f",
                    "rawvideo",
                    "-",
                ]
            )
            planes = np.frombuffer(decoded, "<u2").reshape(3, height, width)
            actual = np.stack((planes[2], planes[0], planes[1]), axis=-1)
            np.testing.assert_array_equal(actual, expected)

    def test_cineon_code_helper_is_the_scan_view_quantizer(self) -> None:
        import v66_profile
        import v44_profile

        e = legacy.model
        v44_profile.apply(e)
        archive_dmin = e.PRINT_2383_DMIN_SPECTRAL_DENSITY.copy()
        archive_mid = e.NEUTRAL_MID_SCANNER_DENSITY.copy()
        archive_high = e.NEUTRAL_HIGH_SCANNER_DENSITY.copy()
        v66_profile.apply(e)
        scanner = np.asarray(
            [[[-0.40, 0.00, 0.70], [0.08, 1.35, 3.00]]],
            dtype=np.float32,
        )
        actual = e.quantized_cineon_code_from_scanner_density(scanner)
        gain = 0.700 / np.maximum(e.NEUTRAL_MID_SCANNER_DENSITY, 1e-6)
        expected = np.clip(
            np.rint(95.0 + scanner * gain / 0.002), 0.0, 1023.0
        ).astype(np.uint16)
        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.dtype, np.uint16)
        np.testing.assert_array_equal(
            e.render_cineon_scan_master_from_scanner_density(scanner),
            e.render_cineon_open_display_from_code(actual),
        )
        np.testing.assert_array_equal(
            render_cineon_view(actual, CineonViewPolicy.OPEN_MONITOR_V66),
            e.render_cineon_open_display_from_code(actual),
        )
        pointwise = render_cineon_view(
            actual, CineonViewPolicy.BLURAY_POINTWISE_V66
        )
        expected_pointwise = e.finish_cineon_scan_for_bluray(
            e.render_cineon_open_display_from_code(actual)
        )
        expected_pointwise = e.compress_oklab_chroma_to_rec709(
            expected_pointwise
        )
        if e.SPIRIT_NEUTRAL_SCALE_CALIBRATION_ENABLED:
            expected_pointwise = e.neutralize_spirit_finished_gray_scale(
                expected_pointwise
            )
        np.testing.assert_array_equal(pointwise, expected_pointwise)
        self.assertTrue(
            POLICY_CONTRACTS[
                CineonViewPolicy.BLURAY_POINTWISE_V66
            ]["pure_function_of_dpx"]
        )
        self.assertFalse(LEGACY_MANAGED_SCAN_CONTRACT["pure_function_of_dpx"])
        v44_profile.apply(e)
        np.testing.assert_array_equal(
            e.PRINT_2383_DMIN_SPECTRAL_DENSITY, archive_dmin
        )
        np.testing.assert_array_equal(e.NEUTRAL_MID_SCANNER_DENSITY, archive_mid)
        np.testing.assert_array_equal(
            e.NEUTRAL_HIGH_SCANNER_DENSITY, archive_high
        )

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

    def test_v45_changes_only_the_official_cie_observer_boundary(self) -> None:
        import v45_profile
        import v44_profile

        e = legacy.model
        v44_profile.apply(e)
        old_lut = e.build_2383_projection_lut()
        config = EngineConfig(profile="v45", mode=EngineMode.REFERENCE)
        v45_profile.apply(e)
        report = research_conformance(e, v45_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(e.PRINT_2383_CMF_MODE, "cie_1931_2deg_official_1nm")
        self.assertEqual(e.PRINT_GRAIN_DOMAIN, "none")
        self.assertEqual(e.PRINT_2383_HYPOTHESIS_COMMON_GRAIN_DENSITY_SCALE, 0.0)
        wavelength, cmf = e._cie_1931_xyz_official_1nm()
        self.assertEqual(wavelength.shape, (401,))
        self.assertEqual(cmf.shape, (401, 3))
        self.assertTrue(np.all(np.isfinite(cmf)))
        new_lut = e.build_2383_projection_lut()
        delta = new_lut.astype(np.float64) - old_lut.astype(np.float64)
        self.assertAlmostEqual(
            float(np.sqrt(np.mean(delta * delta))), 0.004569167554265219
        )
        self.assertLess(float(np.max(np.abs(delta[0, 0, 0]))), 4e-7)
        import v42_profile
        v42_profile.apply(e)
        self.assertEqual(e.PRINT_2383_CMF_MODE, "analytic_20nm")

    def test_public_v48_uses_direct_2383_mean_and_only_manages_grain_delta(self) -> None:
        import v48_release_profile

        config = EngineConfig(profile="v48r", mode=EngineMode.REFERENCE)
        engine = Emulsion5279Engine(config)
        engine.profile = v48_release_profile
        rng = np.random.default_rng(480)
        mean_projection = rng.uniform(0.08, 0.72, (24, 30, 3)).astype(
            np.float32
        )
        mean_scan = rng.uniform(0.08, 0.72, (24, 30, 3)).astype(np.float32)
        formed_projection = np.clip(
            mean_projection
            + rng.normal(0.0, 0.008, mean_projection.shape).astype(np.float32),
            0.0,
            1.0,
        )
        formed_scan = np.clip(
            mean_scan
            + rng.normal(0.0, 0.008, mean_scan.shape).astype(np.float32),
            0.0,
            1.0,
        )
        published, published_mean = engine._publish_projection_pair(
            formed_projection,
            formed_scan,
            mean_projection,
            mean_scan,
        )
        np.testing.assert_array_equal(published_mean, mean_projection)
        managed_formed = engine._publish_projection_colour_v46(
            formed_projection, formed_scan
        )
        managed_mean = engine._publish_projection_colour_v46(
            mean_projection, mean_scan
        )
        expected = np.clip(
            mean_projection + managed_formed - managed_mean, 0.0, 1.0
        ).astype(np.float32)
        np.testing.assert_array_equal(published, expected)
        self.assertGreater(
            float(np.max(np.abs(published_mean - mean_scan))), 0.01
        )

    def test_v48_isolates_isotropic_site_integration_and_v45_resets_it(self) -> None:
        import v45_profile
        import v48_profile

        e = legacy.model
        base_sigma = e.SUBEMULSION_OPTICAL_SIGMA_BASE_PX_5760_RGB.copy()
        config = EngineConfig(profile="v48", mode=EngineMode.REFERENCE)
        v48_profile.apply(e)
        report = research_conformance(e, v48_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(e.GRAIN_SUBPIXEL_PHASE_RADIUS_PX, 0.0)
        self.assertEqual(
            e.GRAIN_SITE_RASTERIZATION_MODE,
            "isotropic_continuous_site_second_moment",
        )
        np.testing.assert_array_equal(
            e.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB,
            np.sqrt(np.square(base_sigma) + 1.0 / 6.0).astype(np.float32),
        )

        v45_profile.apply(e)
        self.assertEqual(e.GRAIN_SUBPIXEL_PHASE_RADIUS_PX, 0.38)
        self.assertEqual(
            e.GRAIN_SITE_RASTERIZATION_MODE,
            "fixed_global_bilinear_phase",
        )
        np.testing.assert_array_equal(
            e.SUBEMULSION_OPTICAL_SIGMA_PX_5760_RGB,
            base_sigma,
        )

    def test_v49_removes_only_the_unmeasured_macro_density_guard(self) -> None:
        import v48_profile
        import v49_profile

        e = legacy.model
        config = EngineConfig(profile="v49", mode=EngineMode.REFERENCE)
        v49_profile.apply(e)
        report = research_conformance(e, v49_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(
            e.GRAIN_LOCAL_DENSITY_BOUND_MODE,
            "nonnegative_microscopic_density",
        )
        self.assertEqual(e.GRAIN_SUBPIXEL_PHASE_RADIUS_PX, 0.0)

        v48_profile.apply(e)
        self.assertEqual(
            e.GRAIN_LOCAL_DENSITY_BOUND_MODE,
            "legacy_macro_dmax_plus_0_12",
        )

    def test_v50_uses_vector_trace_and_v49_restores_archive_curve(self) -> None:
        import v49_profile
        import v50_profile

        e = legacy.model
        config = EngineConfig(profile="v50", mode=EngineMode.REFERENCE)
        v50_profile.apply(e)
        report = research_conformance(e, v50_profile, config)
        self.assertTrue(report["image_model_conformant"])
        np.testing.assert_array_equal(
            e.GRANULARITY_LOG_EXPOSURE,
            v50_profile.GRANULARITY_LOG_EXPOSURE,
        )
        np.testing.assert_array_equal(
            e.GRANULARITY_SIGMA_D_RGB,
            v50_profile.GRANULARITY_SIGMA_D_RGB,
        )
        self.assertEqual(float(e.GRANULARITY_LOG_EXPOSURE[-1]), 0.0)

        v49_profile.apply(e)
        np.testing.assert_array_equal(
            e.GRANULARITY_LOG_EXPOSURE,
            e.GRANULARITY_LOG_EXPOSURE_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e.GRANULARITY_SIGMA_D_RGB,
            e.GRANULARITY_SIGMA_D_RGB_ARCHIVE,
        )

    def test_v51_uses_vector_spectra_and_v50_restores_archive_spectra(self) -> None:
        import v50_profile
        import v51_profile

        e = legacy.model
        v50_profile.apply(e)
        frozen_hd = e.SENSITO_DENSITY_RGB.copy()
        frozen_granularity = e.GRANULARITY_SIGMA_D_RGB.copy()
        frozen_dir = e.DIR_POPULATION_TRANSPORT.copy()
        frozen_mtf = e.NEGATIVE_MTF_CORE_SIGMA_RGB.copy()
        config = EngineConfig(profile="v51", mode=EngineMode.REFERENCE)
        v51_profile.apply(e)
        report = research_conformance(e, v51_profile, config)
        self.assertTrue(report["image_model_conformant"])
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY,
            v51_profile.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY,
        )
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY,
            v51_profile.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY,
        )
        np.testing.assert_array_equal(e.SENSITO_DENSITY_RGB, frozen_hd)
        np.testing.assert_array_equal(
            e.GRANULARITY_SIGMA_D_RGB, frozen_granularity
        )
        np.testing.assert_array_equal(e.DIR_POPULATION_TRANSPORT, frozen_dir)
        np.testing.assert_array_equal(e.NEGATIVE_MTF_CORE_SIGMA_RGB, frozen_mtf)

        v50_profile.apply(e)
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY,
            e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY,
            e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY_ARCHIVE,
        )

    def test_v52_separates_traced_hd_from_inferred_shoulder(self) -> None:
        import v51_profile
        import v52_profile

        e = legacy.model
        v51_profile.apply(e)
        frozen_granularity = e.GRANULARITY_SIGMA_D_RGB.copy()
        frozen_net_spectra = e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY.copy()
        frozen_dmin_spectrum = e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY.copy()
        frozen_dir = e.DIR_POPULATION_TRANSPORT.copy()
        frozen_mtf = e.NEGATIVE_MTF_CORE_SIGMA_RGB.copy()

        config = EngineConfig(profile="v52", mode=EngineMode.REFERENCE)
        v52_profile.apply(e)
        report = research_conformance(e, v52_profile, config)
        self.assertTrue(report["image_model_conformant"])
        np.testing.assert_array_equal(
            e.SENSITO_LOG_EXPOSURE, v52_profile.SENSITO_LOG_EXPOSURE
        )
        np.testing.assert_array_equal(
            e.SENSITO_DENSITY_RGB, v52_profile.SENSITO_DENSITY_RGB
        )
        np.testing.assert_array_equal(e.SENSITO_DMIN_RGB, e.SENSITO_DENSITY_RGB[:, 0])
        self.assertTrue(np.all(np.diff(e.SENSITO_DENSITY_RGB, axis=1) >= 0.0))

        zero = int(np.flatnonzero(e.SENSITO_LOG_EXPOSURE == 0.0)[0])
        archive_zero = int(
            np.flatnonzero(e.SENSITO_LOG_EXPOSURE_ARCHIVE == 0.0)[0]
        )
        np.testing.assert_allclose(
            e.SENSITO_DENSITY_RGB[:, zero + 1 :]
            - e.SENSITO_DENSITY_RGB[:, zero, None],
            e.SENSITO_DENSITY_RGB_ARCHIVE[:, archive_zero + 1 :]
            - e.SENSITO_DENSITY_RGB_ARCHIVE[:, archive_zero, None],
            rtol=0.0,
            atol=3e-7,
        )
        np.testing.assert_array_equal(e.GRANULARITY_SIGMA_D_RGB, frozen_granularity)
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY, frozen_net_spectra
        )
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY, frozen_dmin_spectrum
        )
        np.testing.assert_array_equal(e.DIR_POPULATION_TRANSPORT, frozen_dir)
        np.testing.assert_array_equal(e.NEGATIVE_MTF_CORE_SIGMA_RGB, frozen_mtf)

        neutral = np.repeat(
            e.SENSITO_LOG_EXPOSURE[:, None], 3, axis=1
        ).astype(np.float32)
        np.testing.assert_allclose(
            e.record_densities_from_log_exposure(neutral),
            e.SENSITO_DENSITY_RGB.T,
            rtol=0.0,
            atol=3e-7,
        )

        v51_profile.apply(e)
        np.testing.assert_array_equal(
            e.SENSITO_LOG_EXPOSURE, e.SENSITO_LOG_EXPOSURE_ARCHIVE
        )
        np.testing.assert_array_equal(
            e.SENSITO_DENSITY_RGB, e.SENSITO_DENSITY_RGB_ARCHIVE
        )

    def test_v53_uses_vector_2383_hd_and_v52_restores_archive_print(self) -> None:
        import v52_profile
        import v53_profile

        e = legacy.model
        v53_profile.apply(e)
        config = EngineConfig(profile="v53", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v53_profile, config)
        self.assertTrue(report["image_model_conformant"])
        np.testing.assert_array_equal(
            e.PRINT_2383_LOG_EXPOSURE, v53_profile.PRINT_2383_LOG_EXPOSURE
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_DENSITY_RGB, v53_profile.PRINT_2383_DENSITY_RGB
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_STATUS_A_DMIN_RGB,
            e.PRINT_2383_DENSITY_RGB[:, 0],
        )
        self.assertTrue(np.all(np.diff(e.PRINT_2383_DENSITY_RGB, axis=1) >= 0.0))
        self.assertEqual(float(e.PRINT_2383_LOG_EXPOSURE[0]), -3.0)
        self.assertEqual(float(e.PRINT_2383_LOG_EXPOSURE[-1]), 3.0)

        # V53 changes only the print H-D graph; V52 remains the archive witness
        # for all other 5279/2383 components and must fully restore this table.
        v52_profile.apply(e)
        np.testing.assert_array_equal(
            e.PRINT_2383_LOG_EXPOSURE, e.PRINT_2383_LOG_EXPOSURE_ARCHIVE
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_DENSITY_RGB, e.PRINT_2383_DENSITY_RGB_ARCHIVE
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_STATUS_A_DMIN_RGB,
            e.PRINT_2383_STATUS_A_DMIN_RGB_ARCHIVE,
        )
        self.assertEqual(e.PRINT_2383_DMAX, e.PRINT_2383_DMAX_ARCHIVE)

    def test_v54_isolates_2383_record_sensitivity_and_v53_restores_it(self) -> None:
        import v53_profile
        import v54_profile

        e = legacy.model
        v54_profile.apply(e)
        config = EngineConfig(profile="v54", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v54_profile, config)
        self.assertTrue(report["image_model_conformant"])
        np.testing.assert_array_equal(
            e.PRINT_2383_LOG_SENSITIVITY_CMY,
            v54_profile.PRINT_2383_LOG_SENSITIVITY_CMY,
        )
        np.testing.assert_array_equal(
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY,
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e.KODAK_XENON_PROJECTOR_RELATIVE_SPD,
            e.KODAK_XENON_PROJECTOR_RELATIVE_SPD_ARCHIVE,
        )

        v53_profile.apply(e)
        np.testing.assert_array_equal(
            e.PRINT_2383_LOG_SENSITIVITY_CMY,
            e.PRINT_2383_LOG_SENSITIVITY_CMY_ARCHIVE,
        )

    def test_v55_isolates_2383_dye_spectra_and_v54_restores_them(self) -> None:
        import v54_profile
        import v55_profile

        e = legacy.model
        v55_profile.apply(e)
        config = EngineConfig(profile="v55", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v55_profile, config)
        self.assertTrue(report["image_model_conformant"])
        np.testing.assert_array_equal(
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY,
            v55_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY,
        )
        np.testing.assert_array_equal(
            np.argmax(e.PRINT_DYE_CMY_SPECTRAL_DENSITY, axis=0),
            np.asarray([14, 8, 3]),
        )
        np.testing.assert_array_equal(
            e.KODAK_XENON_PROJECTOR_RELATIVE_SPD,
            e.KODAK_XENON_PROJECTOR_RELATIVE_SPD_ARCHIVE,
        )

        v54_profile.apply(e)
        np.testing.assert_array_equal(
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY,
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY_ARCHIVE,
        )

    def test_v56_changes_only_projection_monitor_colour_authority(self) -> None:
        import v55_profile
        import v56_profile

        e = legacy.model
        v56_profile.apply(e)
        config = EngineConfig(profile="v56", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v56_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(
            e.PRINT_MONITOR_COLOUR_AUTHORITY, "physical_spectral_v56"
        )
        np.testing.assert_array_equal(
            e.PRINT_DYE_CMY_SPECTRAL_DENSITY,
            v56_profile.PRINT_DYE_CMY_SPECTRAL_DENSITY,
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_LOG_SENSITIVITY_CMY,
            v56_profile.PRINT_2383_LOG_SENSITIVITY_CMY,
        )

        v55_profile.apply(e)
        self.assertEqual(
            e.PRINT_MONITOR_COLOUR_AUTHORITY,
            e.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE,
        )

    def test_v57_brackets_unidentified_2383_interimage_with_identity(self) -> None:
        import v56_profile
        import v57_profile

        e = legacy.model
        v57_profile.apply(e)
        config = EngineConfig(profile="v57", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v57_profile, config)
        self.assertTrue(report["image_model_conformant"])
        np.testing.assert_array_equal(
            e.PRINT_2383_INTERIMAGE_MATRIX, np.eye(3, dtype=np.float32)
        )
        self.assertEqual(
            e.PRINT_MONITOR_COLOUR_AUTHORITY, "physical_spectral_v56"
        )

        v56_profile.apply(e)
        np.testing.assert_array_equal(
            e.PRINT_2383_INTERIMAGE_MATRIX,
            e.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE,
        )

    def test_v58_resolves_integral_lad_into_principal_curve_density(self) -> None:
        import v55_profile
        import v58_profile

        e = legacy.model
        v58_profile.apply(e)
        config = EngineConfig(profile="v58", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v58_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(
            e.PRINT_2383_LAD_PRINCIPAL_POLICY,
            "integral_spectral_inverse_v58",
        )
        np.testing.assert_allclose(
            e.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB,
            [0.9898583, 0.8823338, 0.8419376],
            rtol=0.0,
            atol=2e-6,
        )
        np.testing.assert_allclose(
            e.PRINT_2383_LAD_INTEGRAL_RESIDUAL_RGB,
            np.zeros(3),
            rtol=0.0,
            atol=1e-7,
        )
        neutral_negative = e.negative_total_printer_density(
            np.full(3, 0.18, dtype=np.float32)
        )
        neutral_print = e.print_2383_density_from_negative(neutral_negative)
        np.testing.assert_allclose(
            neutral_print,
            e.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB,
            rtol=0.0,
            atol=2e-7,
        )

        # The coordinate correction must not become an interimage or observer
        # change, and V55 must still reproduce the archived interpretation.
        np.testing.assert_array_equal(
            e.PRINT_2383_INTERIMAGE_MATRIX,
            e.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE,
        )
        self.assertEqual(
            e.PRINT_MONITOR_COLOUR_AUTHORITY,
            e.PRINT_MONITOR_COLOUR_AUTHORITY_ARCHIVE,
        )
        v55_profile.apply(e)
        self.assertEqual(
            e.PRINT_2383_LAD_PRINCIPAL_POLICY,
            e.PRINT_2383_LAD_PRINCIPAL_POLICY_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e._active_2383_lad_principal_density_rgb(),
            e.PRINT_2383_LAD_STATUS_A_AIM_RGB,
        )

    def test_v59_restores_vector_traced_2383_visual_neutral_base(self) -> None:
        import v58_profile
        import v59_profile

        e = legacy.model
        v59_profile.apply(e)
        config = EngineConfig(profile="v59", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v59_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(
            e.PRINT_2383_DMIN_SPECTRAL_POLICY,
            "vector_neutral_residual_v59",
        )
        self.assertEqual(
            e.PRINT_2383_LAD_PRINCIPAL_POLICY,
            "integral_spectral_inverse_v59",
        )
        dye_sum = np.sum(e.PRINT_DYE_CMY_SPECTRAL_DENSITY, axis=1)
        np.testing.assert_allclose(
            e.PRINT_2383_DMIN_SPECTRAL_DENSITY + dye_sum,
            v59_profile.PRINT_2383_VISUAL_NEUTRAL_SPECTRAL_DENSITY,
            rtol=0.0,
            atol=2e-7,
        )
        np.testing.assert_allclose(
            e.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB,
            [0.99258363, 0.8840549, 0.8475401],
            rtol=0.0,
            atol=2e-6,
        )
        status_a, amounts = (
            e.integral_status_a_from_2383_principal_density_rgb(
                e.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB
            )
        )
        np.testing.assert_allclose(
            status_a,
            e.PRINT_2383_LAD_STATUS_A_AIM_RGB,
            rtol=0.0,
            atol=2e-7,
        )
        np.testing.assert_allclose(
            amounts,
            [1.0270529, 0.9971411, 0.9746268],
            rtol=0.0,
            atol=2e-6,
        )

        # Profile changes in one interpreter must not leak the spectral base
        # into V58 or any older profile.
        v58_profile.apply(e)
        self.assertEqual(
            e.PRINT_2383_DMIN_SPECTRAL_POLICY,
            e.PRINT_2383_DMIN_SPECTRAL_POLICY_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_DMIN_SPECTRAL_DENSITY,
            e.PRINT_2383_DMIN_SPECTRAL_DENSITY_ARCHIVE,
        )

    def test_v60_registers_spectral_base_to_hd_curve_dmin(self) -> None:
        import v59_profile
        import v60_profile

        e = legacy.model
        v60_profile.apply(e)
        config = EngineConfig(profile="v60", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v60_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(
            e.PRINT_2383_DMIN_SPECTRAL_POLICY,
            "vector_neutral_residual_dmin_registered_v60",
        )
        axes = e._print_2383_analytical_amount_axes(
            e.PRINT_2383_STATUS_A_DMIN_RGB
        )
        np.testing.assert_allclose(
            [axes[channel][channel] for channel in range(3)],
            np.zeros(3),
            rtol=0.0,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            e.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB,
            [0.9897172, 0.8820604, 0.84214854],
            rtol=0.0,
            atol=2e-6,
        )
        status_a, amounts = (
            e.integral_status_a_from_2383_principal_density_rgb(
                e.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB
            )
        )
        np.testing.assert_allclose(
            status_a,
            e.PRINT_2383_LAD_STATUS_A_AIM_RGB,
            rtol=0.0,
            atol=2e-7,
        )
        np.testing.assert_allclose(
            amounts,
            [1.0550362, 1.0296745, 0.9633866],
            rtol=0.0,
            atol=2e-6,
        )

        # V59 remains reproducible as the unregistered intermediate finding.
        v59_profile.apply(e)
        self.assertEqual(
            e.PRINT_2383_DMIN_SPECTRAL_POLICY,
            "vector_neutral_residual_v59",
        )
        np.testing.assert_allclose(
            e.PRINT_2383_LAD_ANALYTICAL_AMOUNT_CMY,
            [1.0270529, 0.9971411, 0.9746268],
            rtol=0.0,
            atol=2e-6,
        )

    def test_v61_joint_iso_status_m_negative_coordinate(self) -> None:
        import v60_profile
        import v61_profile

        e = legacy.model
        v61_profile.apply(e)
        config = EngineConfig(profile="v61", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v61_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertEqual(
            e.NEGATIVE_5279_STATUS_M_POLICY,
            "iso5_3_spectral_products_1nm_v61",
        )
        self.assertEqual(
            e.NEGATIVE_5279_ANALYTICAL_DENSITY_POLICY,
            "joint_iso_status_m_v61",
        )
        wavelengths = e.NEGATIVE_5279_STATUS_M_WAVELENGTHS_NM
        weights = e.NEGATIVE_5279_STATUS_M_RGB_WEIGHTS
        np.testing.assert_array_equal(
            wavelengths[np.argmax(weights, axis=0)],
            [640.0, 540.0, 450.0],
        )
        analytical = np.asarray(
            [0.47126241, 0.61012430, 0.73570945], dtype=np.float32
        )
        status_m = e.negative_5279_status_m_net_density_from_analytical_cmy(
            analytical
        )
        recovered = e.solve_5279_analytical_cmy_from_status_m_net_density(
            status_m
        )
        np.testing.assert_allclose(recovered, analytical, rtol=0.0, atol=2e-6)
        np.testing.assert_allclose(
            e.negative_5279_status_m_net_density_from_analytical_cmy(
                np.zeros(3, dtype=np.float32)
            ),
            np.zeros(3),
            rtol=0.0,
            atol=1e-7,
        )

        # V61 must not leak its ISO receiver or joint inverse into V60.
        v60_profile.apply(e)
        self.assertEqual(
            e.NEGATIVE_5279_STATUS_M_POLICY,
            e.NEGATIVE_5279_STATUS_M_POLICY_ARCHIVE,
        )
        self.assertEqual(
            e.NEGATIVE_5279_ANALYTICAL_DENSITY_POLICY,
            e.NEGATIVE_5279_ANALYTICAL_DENSITY_POLICY_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_STATUS_M_RGB_WEIGHTS,
            e.NEGATIVE_5279_STATUS_M_RGB_WEIGHTS_ARCHIVE,
        )

    def test_v62_withholds_unmeasured_interimage_and_owns_lattice(self) -> None:
        import v61_profile
        import v62_profile

        from .assets import projection_lattice_for_profile

        e = legacy.model
        v62_profile.apply(e)
        config = EngineConfig(profile="v62", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v62_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(
            e.PRINT_2383_INTERIMAGE_POLICY,
            "unmeasured_identity_withheld_v62",
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_INTERIMAGE_MATRIX, np.eye(3, dtype=np.float32)
        )
        lattice = projection_lattice_for_profile("v62")
        self.assertEqual(
            lattice.sha256,
            "b26660989bc9d5baaa4719e21e9f41a1b9b9d85729ab228316a15914de75b22e",
        )

        # V62's evidence boundary must not leak back into the reproducible V61.
        v61_profile.apply(e)
        self.assertEqual(
            e.PRINT_2383_INTERIMAGE_POLICY,
            e.PRINT_2383_INTERIMAGE_POLICY_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e.PRINT_2383_INTERIMAGE_MATRIX,
            e.PRINT_2383_INTERIMAGE_MATRIX_ARCHIVE,
        )

    def test_v63_uses_actual_neutral_trajectory_and_owns_lattice(self) -> None:
        import v62_profile
        import v63_profile

        from .assets import projection_lattice_for_profile

        e = legacy.model
        v63_profile.apply(e)
        config = EngineConfig(profile="v63", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v63_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(
            e.PRINT_2383_VIEW_NEUTRAL_POLICY,
            "actual_5279_to_2383_neutral_trajectory_v63",
        )
        self.assertEqual(e.PRINT_MONITOR_COLOUR_AUTHORITY, "scan_referenced_v31")
        self.assertEqual(e.PRINT_MONITOR_CHROMA_ADAPTATION, "absolute_chroma")
        np.testing.assert_array_equal(
            e.PRINT_2383_INTERIMAGE_MATRIX, np.eye(3, dtype=np.float32)
        )
        lattice = projection_lattice_for_profile("v63")
        self.assertEqual(
            lattice.sha256,
            "ef861a38d840b30fa0dd2b9a6f01b41c8122600daea13e43dcb6ee49bfa67024",
        )

        # V63's observer coordinate must not leak back into V62.
        v62_profile.apply(e)
        self.assertEqual(
            e.PRINT_2383_VIEW_NEUTRAL_POLICY,
            e.PRINT_2383_VIEW_NEUTRAL_POLICY_ARCHIVE,
        )

    def test_v64_withdraws_only_unmeasured_print_density_shaper(self) -> None:
        import v63_profile
        import v64_profile

        from .assets import projection_lattice_for_profile

        e = legacy.model
        v64_profile.apply(e)
        config = EngineConfig(profile="v64", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v64_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(
            e.PRINT_2383_DENSITY_NEUTRAL_POLICY,
            "published_separated_status_a_curves_unshaped_v64",
        )
        negative = np.asarray(
            [[[0.2, 0.7, 1.1], [1.4, 0.9, 0.3]]], dtype=np.float32
        )
        np.testing.assert_array_equal(
            e.print_2383_density_from_negative(negative),
            e._raw_print_2383_density_from_negative(negative),
        )
        lattice = projection_lattice_for_profile("v64")
        self.assertEqual(
            lattice.sha256,
            "27203fdc8407c446fae65b9f259677cdd8320cdb1ec95961c859105cf211bd32",
        )

        # The evidence withdrawal must not leak into the reproducible V63.
        v63_profile.apply(e)
        self.assertEqual(
            e.PRINT_2383_DENSITY_NEUTRAL_POLICY,
            e.PRINT_2383_DENSITY_NEUTRAL_POLICY_ARCHIVE,
        )

    def test_v66_uses_cineon_printing_density_and_restores_v64(self) -> None:
        import v64_profile
        import v66_profile

        from .assets import projection_lattice_for_profile

        e = legacy.model
        sample = np.asarray(
            [[[0.22, 0.58, 1.12], [1.40, 0.90, 0.30]]],
            dtype=np.float32,
        )

        v64_profile.apply(e)
        archive = e.scanner_density_from_total_record_density(sample)
        self.assertEqual(
            e.SPIRIT_PRIMARY_CORRECTION_TARGET,
            e.SPIRIT_PRIMARY_CORRECTION_TARGET_ARCHIVE,
        )

        v66_profile.apply(e)
        config = EngineConfig(profile="v66", mode=EngineMode.REFERENCE)
        report = research_conformance(e, v66_profile, config)
        self.assertTrue(report["image_model_conformant"])
        self.assertTrue(all(report["checks"].values()))
        base = e.negative_total_printer_density_from_record_density(
            e.SENSITO_DMIN_RGB
        )
        expected = (
            e.negative_total_printer_density_from_record_density(sample) - base
        )
        np.testing.assert_array_equal(
            e.scanner_density_from_total_record_density(sample), expected
        )
        self.assertFalse(np.array_equal(archive, expected))
        lattice = projection_lattice_for_profile("v66")
        self.assertEqual(
            lattice.sha256,
            "03ce9d14a785776121cd33ad76fe7efef222c08a0aee14611f04d10fdb1049ad",
        )

        # The new Cineon coordinate must not leak into reproducible V64.
        v64_profile.apply(e)
        self.assertEqual(
            e.SPIRIT_PRIMARY_CORRECTION_TARGET,
            e.SPIRIT_PRIMARY_CORRECTION_TARGET_ARCHIVE,
        )
        np.testing.assert_array_equal(
            e.scanner_density_from_total_record_density(sample), archive
        )

    def test_v72_withdraws_only_direct_record_mix_and_v66_restores_it(self) -> None:
        import v66_profile
        import v72_profile

        from .assets import projection_lattice_for_profile

        e = legacy.model
        v66_profile.apply(e)
        v66_mix = e.SUBEMULSION_DYE_RECORD_MIX.copy()
        frozen = {
            "granularity": e.GRANULARITY_SIGMA_D_RGB.copy(),
            "sensitometry": e.SENSITO_DENSITY_RGB.copy(),
            "negative_spectra": (
                e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY.copy()
            ),
            "dir_transport": e.DIR_POPULATION_TRANSPORT.copy(),
            "dir_strength": e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH,
            "mtf_core": e.NEGATIVE_MTF_CORE_SIGMA_RGB.copy(),
        }

        v72_profile.apply(e)
        report = research_conformance(
            e,
            v72_profile,
            EngineConfig(profile="v72", mode=EngineMode.REFERENCE),
        )
        self.assertTrue(report["image_model_conformant"])
        self.assertTrue(all(report["checks"].values()))
        np.testing.assert_array_equal(
            e.SUBEMULSION_DYE_RECORD_MIX,
            np.repeat(np.eye(3, dtype=np.float32)[None, ...], 3, axis=0),
        )
        np.testing.assert_array_equal(e.GRANULARITY_SIGMA_D_RGB, frozen["granularity"])
        np.testing.assert_array_equal(e.SENSITO_DENSITY_RGB, frozen["sensitometry"])
        np.testing.assert_array_equal(
            e.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY,
            frozen["negative_spectra"],
        )
        np.testing.assert_array_equal(e.DIR_POPULATION_TRANSPORT, frozen["dir_transport"])
        self.assertEqual(
            e.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH, frozen["dir_strength"]
        )
        np.testing.assert_array_equal(e.NEGATIVE_MTF_CORE_SIGMA_RGB, frozen["mtf_core"])
        self.assertEqual(
            projection_lattice_for_profile("v72").sha256,
            projection_lattice_for_profile("v66").sha256,
        )

        v66_profile.apply(e)
        np.testing.assert_array_equal(e.SUBEMULSION_DYE_RECORD_MIX, v66_mix)

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

    def test_shared_negative_exposure_fields_are_bit_exact(self) -> None:
        """Mean and stochastic formation may reuse one exposure/activation field."""
        e = legacy.model
        legacy.profile.apply(e)
        rng = np.random.default_rng(527944)
        records = rng.uniform(0.01, 4.0, (36, 48, 3)).astype(np.float32)
        log_exposure = np.log10(np.maximum(records, 1e-8)) - 1.0
        activations = e.subemulsion_activation_probabilities(log_exposure)
        expected_mean = e.develop_5279_record_density(records)
        shared_mean = e.develop_5279_record_density_from_log_exposure(
            log_exposure,
            precomputed_activations=activations,
        )
        np.testing.assert_array_equal(shared_mean, expected_mean)
        expected_formed = e.form_5279_multilayer_record_density(
            records,
            44,
            1.0,
            1,
            precomputed_mean_density=expected_mean,
        )
        shared_formed = e.form_5279_multilayer_record_density(
            records,
            44,
            1.0,
            1,
            precomputed_mean_density=shared_mean,
            precomputed_log_exposure=log_exposure,
            precomputed_activations=activations,
        )
        np.testing.assert_array_equal(shared_formed, expected_formed)

    def test_neutral_multilayer_development_stays_on_published_hd(self) -> None:
        """Layer decomposition must not create a second neutral H-D curve."""
        e = legacy.model
        legacy.profile.apply(e)
        for log_exposure in np.linspace(-4.0, 1.0, 21, dtype=np.float32):
            field = np.full((12, 16, 3), log_exposure, dtype=np.float32)
            published = e.record_densities_from_log_exposure(field)
            developed = e.develop_5279_record_density_from_log_exposure(field)
            np.testing.assert_allclose(
                developed,
                published,
                rtol=0.0,
                atol=3.0e-7,
            )

    def test_zero_physical_colour_authority_skips_unreachable_calibration(self) -> None:
        """V31+'s zero colour weights cannot consume calibrated physical RGB."""
        e = legacy.model
        legacy.profile.apply(e)
        self.assertEqual(e.PRINT_MONITOR_PHYSICAL_HUE_WEIGHT, 0.0)
        self.assertEqual(e.PRINT_MONITOR_PHYSICAL_SATURATION_WEIGHT, 0.0)
        rng = np.random.default_rng(238331)
        density = rng.uniform(0.08, 2.4, (10, 12, 3)).astype(np.float32)
        print_density = rng.uniform(0.05, 3.6, density.shape).astype(np.float32)

        original = e._calibrate_2383_projected_view

        def unreachable(*_args, **_kwargs):
            raise AssertionError("withdrawn physical colour branch was evaluated")

        e._calibrate_2383_projected_view = unreachable
        try:
            result = e._render_2383_monitor_projection_base_from_record_density(
                density,
                print_density=print_density,
            )
        finally:
            e._calibrate_2383_projected_view = original
        self.assertEqual(result.shape, density.shape)
        self.assertTrue(np.all(np.isfinite(result)))

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
            return_cineon_code=True,
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            parallel = e.reconstruct_density_pair_to_dual_display_v39(
                mean,
                formed,
                17,
                1.0,
                "linear_rec709",
                return_mean_pair=True,
                return_cineon_code=True,
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

    def test_oklab_lightness_only_is_bit_exact(self) -> None:
        """The zero-retention adapter may omit unused OKLab opponent channels."""
        e = legacy.model
        rng = np.random.default_rng(4400)
        rgb = rng.uniform(-0.1, 1.1, (72, 96, 3)).astype(np.float32)
        expected = e.linear_rec709_to_oklab(rgb)[..., 0]
        actual = e.linear_rec709_to_oklab_lightness(rgb)
        np.testing.assert_array_equal(actual, expected)

    def test_fused_oklab_forward_transform_is_bit_exact(self) -> None:
        """The production 2383 observer may fuse only an exact OKLab direction."""
        import pipeline_accel

        e = legacy.model
        rng = np.random.default_rng(238344)
        rgb = rng.uniform(-0.1, 1.1, (72, 96, 3)).astype(np.float32)
        rgb_to_lms = np.array(
            [
                [0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005],
            ],
            dtype=np.float32,
        )
        lms_to_lab = np.array(
            [
                [0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660],
            ],
            dtype=np.float32,
        )
        expected = e.linear_rec709_to_oklab(rgb)
        actual = pipeline_accel.linear_rec709_to_oklab_fused(
            rgb, rgb_to_lms, lms_to_lab
        )
        np.testing.assert_array_equal(actual, expected)
        expected_l = e.linear_rec709_to_oklab_lightness(rgb)
        actual_l = pipeline_accel.linear_rec709_to_oklab_lightness_fused(
            rgb, rgb_to_lms, lms_to_lab[0]
        )
        np.testing.assert_array_equal(actual_l, expected_l)

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
