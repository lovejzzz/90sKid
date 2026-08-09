from __future__ import annotations

import unittest

import cv2
import numpy as np

import emulsion_experiment as emulsion
import metal_binomial_bridge
import wavefront_tile_lab_v010 as lab


class DummyModule:
    disk_kernel = staticmethod(emulsion.disk_kernel)


class WavefrontTileLabV010Tests(unittest.TestCase):
    def test_population_batch_matches_cpu_float32_precision(self) -> None:
        rng = np.random.default_rng(43)
        probability = rng.random((73, 109), dtype=np.float32)
        module = DummyModule()
        recorded = []
        module._V35_RECORD_BINOMIAL_CALL = (
            lambda site_count, sample_seed: recorded.append(
                (site_count, sample_seed)
            )
        )
        module._V35_METAL_DOMAIN_SALT = 0
        specs = [
            (
                float(weight),
                radius,
                sigma,
                23 + index,
                offset,
                30_000_000 + index,
            )
            for index, (weight, radius, sigma, offset) in enumerate(
                zip(
                    (0.07, 0.13, 0.20, 0.27, 0.33),
                    (0.79, 1.00, 1.25, 1.56, 1.98),
                    (0.46, 0.52, 0.59, 0.66, 0.74),
                    (
                        (0.13, -0.17),
                        (-0.19, 0.11),
                        (0.07, 0.21),
                        (-0.05, -0.13),
                        (0.17, 0.03),
                    ),
                )
            )
        ]
        reference = np.zeros_like(probability)
        for spec in specs:
            weight, radius, sigma, sites, offset, seed = spec
            sample = metal_binomial_bridge.sample(
                probability,
                sites,
                seed,
                mode="bernoulli",
            )
            sample /= float(sites)
            kernel = emulsion.disk_kernel(radius)
            kernel /= float(kernel.sum())
            filtered_sample = cv2.filter2D(
                sample, -1, kernel, borderType=cv2.BORDER_REFLECT
            )
            expected = cv2.filter2D(
                probability, -1, kernel, borderType=cv2.BORDER_REFLECT
            )
            filtered_sample = cv2.GaussianBlur(
                filtered_sample,
                (0, 0),
                sigma,
                borderType=cv2.BORDER_REFLECT,
            )
            expected = cv2.GaussianBlur(
                expected,
                (0, 0),
                sigma,
                borderType=cv2.BORDER_REFLECT,
            )
            deviation = (filtered_sample - expected).astype(np.float32)
            transform = np.array(
                [[1.0, 0.0, offset[0]], [0.0, 1.0, offset[1]]],
                dtype=np.float32,
            )
            deviation = cv2.warpAffine(
                deviation,
                transform,
                (probability.shape[1], probability.shape[0]),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT,
            )
            reference += weight * deviation

        actual = lab.population_optical_batch(
            module,
            probability,
            rng,
            specs,
        )
        np.testing.assert_allclose(actual, reference, rtol=0.0, atol=3e-7)
        self.assertEqual(len(recorded), 5)

    def test_phase_matches_opencv_fixed_point_affine_setup(self) -> None:
        from metal_emulsion_batch_bridge import _opencv_effective_translation

        self.assertEqual(
            _opencv_effective_translation(
                0.12295123736316517,
                0.3595594432508575,
            ),
            (0.125, 0.34375),
        )

    def test_install_is_explicit_and_reversible(self) -> None:
        module = DummyModule()
        module._V35_RECORD_BINOMIAL_CALL = lambda *args: None
        lab.install(module, marginal_tile_pixels=250_000)
        self.assertEqual(module._WAVEFRONT_TILE_LAB_VERSION, "0.1.0")
        self.assertTrue(callable(module._WAVEFRONT_POPULATION_OPTICAL_BATCH))
        lab.uninstall(module)
        self.assertFalse(
            hasattr(module, "_WAVEFRONT_POPULATION_OPTICAL_BATCH")
        )


if __name__ == "__main__":
    unittest.main()
