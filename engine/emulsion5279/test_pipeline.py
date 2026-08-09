from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from .contracts import DeliveryEncoding, EngineConfig, EngineMode, ObserverPair
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


if __name__ == "__main__":
    unittest.main()
