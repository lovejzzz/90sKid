from __future__ import annotations

import unittest

import numpy as np

import wavefront_tile_lab_v001 as lab


class DummyModule:
    pass


class WavefrontTileLabV001Tests(unittest.TestCase):
    def test_inplace_marginal_is_float32_bit_exact_across_tiles(self) -> None:
        rng = np.random.default_rng(5279)
        source = rng.random((73, 109, 3, 3), dtype=np.float32)
        expected = np.clip(4.0 * source * (1.0 - source), 0.0, 1.0)
        for tile_pixels in (109, 1_000, 5_000, 100_000):
            with self.subTest(tile_pixels=tile_pixels):
                actual = source.copy()
                returned = lab.activation_marginal_inplace(
                    actual, tile_pixels=tile_pixels
                )
                self.assertIs(returned, actual)
                np.testing.assert_array_equal(actual, expected)

    def test_contract_rejects_wrong_dtype_or_layout(self) -> None:
        with self.assertRaises(ValueError):
            lab.activation_marginal_inplace(
                np.zeros((8, 8, 3, 3), dtype=np.float64), tile_pixels=64
            )
        with self.assertRaises(ValueError):
            lab.activation_marginal_inplace(
                np.zeros((8, 8, 3), dtype=np.float32), tile_pixels=64
            )

    def test_install_is_explicit_and_reversible(self) -> None:
        module = DummyModule()
        lab.install(module, tile_pixels=250_000)
        self.assertEqual(module._WAVEFRONT_TILE_LAB_VERSION, "0.0.1")
        self.assertEqual(
            module._WAVEFRONT_INPLACE_MARGINAL_TILE_PIXELS, 250_000
        )
        lab.uninstall(module)
        self.assertFalse(hasattr(module, "_WAVEFRONT_TILE_LAB_VERSION"))


if __name__ == "__main__":
    unittest.main()
