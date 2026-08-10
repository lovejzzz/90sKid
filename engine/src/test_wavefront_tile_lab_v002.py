from __future__ import annotations

import unittest

import cv2
import numpy as np

import emulsion_experiment as emulsion
import wavefront_tile_lab_v002 as lab


class DummyModule:
    pass


class WavefrontTileLabV002Tests(unittest.TestCase):
    def test_optical_buffers_are_float32_bit_exact(self) -> None:
        rng = np.random.default_rng(5279)
        for radius, sigma, offset in (
            (0.2, 0.05, (0.0, 0.0)),
            (0.9, 0.31, (0.13, -0.17)),
            (2.4, 1.2, (0.0, 0.0)),
        ):
            with self.subTest(radius=radius, sigma=sigma, offset=offset):
                sampled_source = rng.random((73, 109), dtype=np.float32)
                expected_source = rng.random((73, 109), dtype=np.float32)
                kernel = emulsion.disk_kernel(radius)
                kernel /= float(kernel.sum())
                sampled = cv2.filter2D(
                    sampled_source,
                    -1,
                    kernel,
                    borderType=cv2.BORDER_REFLECT,
                )
                expected = cv2.filter2D(
                    expected_source,
                    -1,
                    kernel,
                    borderType=cv2.BORDER_REFLECT,
                )
                sampled = cv2.GaussianBlur(
                    sampled,
                    (0, 0),
                    max(sigma, 0.05),
                    borderType=cv2.BORDER_REFLECT,
                )
                expected = cv2.GaussianBlur(
                    expected,
                    (0, 0),
                    max(sigma, 0.05),
                    borderType=cv2.BORDER_REFLECT,
                )
                reference = (sampled - expected).astype(np.float32, copy=False)
                if offset != (0.0, 0.0):
                    transform = np.array(
                        [[1.0, 0.0, offset[0]], [0.0, 1.0, offset[1]]],
                        dtype=np.float32,
                    )
                    reference = cv2.warpAffine(
                        reference,
                        transform,
                        (reference.shape[1], reference.shape[0]),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_REFLECT,
                    )

                actual_sampled = sampled_source.copy()
                actual_expected = cv2.filter2D(
                    expected_source,
                    -1,
                    kernel,
                    borderType=cv2.BORDER_REFLECT,
                )
                actual = lab.optical_deviation_inplace(
                    actual_sampled,
                    actual_expected,
                    kernel,
                    sigma,
                    offset,
                )
                self.assertIs(actual, actual_sampled)
                np.testing.assert_array_equal(actual, reference)

    def test_class_accumulation_consumes_deviation_exactly(self) -> None:
        rng = np.random.default_rng(43)
        population = rng.normal(size=(72, 96)).astype(np.float32)
        deviation = rng.normal(size=population.shape).astype(np.float32)
        weight = 0.137
        expected = population.copy()
        expected += weight * deviation
        actual_population = population.copy()
        actual_deviation = deviation.copy()
        lab.weight_and_accumulate_class(
            actual_population, actual_deviation, weight
        )
        np.testing.assert_array_equal(actual_population, expected)

    def test_install_inherits_v001_and_is_reversible(self) -> None:
        module = DummyModule()
        lab.install(module, marginal_tile_pixels=250_000)
        self.assertEqual(module._WAVEFRONT_TILE_LAB_VERSION, "0.0.2")
        self.assertTrue(module._WAVEFRONT_INPLACE_OPTICAL_BUFFERS)
        self.assertTrue(module._WAVEFRONT_INPLACE_CLASS_ACCUMULATION)
        self.assertEqual(
            module._WAVEFRONT_INPLACE_MARGINAL_TILE_PIXELS, 250_000
        )
        lab.uninstall(module)
        self.assertFalse(hasattr(module, "_WAVEFRONT_TILE_LAB_VERSION"))


if __name__ == "__main__":
    unittest.main()
