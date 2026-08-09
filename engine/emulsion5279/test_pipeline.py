from __future__ import annotations

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
from .io import DualDeliveryWriter
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
        experimental = EngineConfig(
            exposure_stops=0.0,
            research_baseline=False,
            mode=EngineMode.REFERENCE,
        )
        self.assertFalse(experimental.research_baseline)

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


if __name__ == "__main__":
    unittest.main()
