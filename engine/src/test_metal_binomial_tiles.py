from __future__ import annotations

import sys
import unittest

import numpy as np

import metal_binomial_bridge as metal


@unittest.skipUnless(sys.platform == "darwin", "Metal conformance needs macOS")
class MetalBinomialTileTests(unittest.TestCase):
    def test_row_wavefront_preserves_full_frame_philox_identity(self) -> None:
        height, width = 79, 113
        probability = np.linspace(
            1e-6, 0.986325, height * width, dtype=np.float32
        ).reshape(height, width)
        seed = (0x5279 << 32) | 30_000_000
        expected = metal.sample(
            probability, 23, seed, mode="bernoulli"
        )
        for workset in (width, 500, 1_000, 5_000):
            with self.subTest(workset=workset):
                actual = metal.submit_tiled(
                    probability,
                    23,
                    seed,
                    workset_pixels=workset,
                    in_flight=3,
                    mode="bernoulli",
                ).wait()
                np.testing.assert_array_equal(actual, expected)

    def test_wavefront_rejects_a_partial_row_workset(self) -> None:
        probability = np.full((8, 16), 0.5, dtype=np.float32)
        with self.assertRaises(ValueError):
            metal.submit_tiled(
                probability,
                7,
                30_000_000,
                workset_pixels=15,
                mode="bernoulli",
            )


if __name__ == "__main__":
    unittest.main()
