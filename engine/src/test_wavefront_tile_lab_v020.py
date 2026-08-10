from __future__ import annotations

import unittest

import numpy as np

from engine.emulsion5279 import legacy
from engine.emulsion5279.contracts import EngineConfig, EngineMode
from engine.emulsion5279.pipeline import Emulsion5279Engine

import wavefront_tile_lab_v020


class WavefrontTileLabV020Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = Emulsion5279Engine(
            EngineConfig(profile="v43h", mode=EngineMode.PRODUCTION_METAL)
        )
        cls.engine.configure()

    def tearDown(self) -> None:
        if hasattr(
            legacy.model,
            "_WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL",
        ):
            wavefront_tile_lab_v020.uninstall(legacy.model)

    def test_collapsed_residual_matches_camera_domain_samples(self) -> None:
        module = legacy.model
        reference = module.apply_input_chroma_residual
        composite, d65_y = wavefront_tile_lab_v020._composite_input_residual(
            module
        )
        rng = np.random.default_rng(5279)
        source = rng.uniform(0.0, 8.0, (96, 128, 3)).astype(np.float32)
        expected = reference(source)
        module._WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL = reference
        try:
            actual = wavefront_tile_lab_v020.apply_input_chroma_residual_collapsed(
                module,
                source,
                composite,
                d65_y,
            )
        finally:
            delattr(
                module,
                "_WAVEFRONT_V020_REFERENCE_INPUT_CHROMA_RESIDUAL",
            )
        difference = np.abs(actual - expected)
        self.assertLess(float(difference.max()), 2e-5)
        self.assertLess(
            float(np.sqrt(np.mean(difference.astype(np.float64) ** 2))),
            1e-6,
        )

    def test_install_and_uninstall_restore_reference(self) -> None:
        module = legacy.model
        reference = module.apply_input_chroma_residual
        wavefront_tile_lab_v020.install(module)
        self.assertEqual(module._WAVEFRONT_TILE_LAB_VERSION, "0.2.0")
        self.assertIsNot(module.apply_input_chroma_residual, reference)
        wavefront_tile_lab_v020.uninstall(module)
        self.assertIs(module.apply_input_chroma_residual, reference)

    def test_mean_dir_batch_matches_scalar_reference(self) -> None:
        module = legacy.model
        rng = np.random.default_rng(2383)
        departure = rng.normal(0.0, 0.1, (47, 61, 3, 3)).astype(np.float32)
        marginal = rng.uniform(0.0, 1.0, departure.shape).astype(np.float32)
        net_capacity = (
            module.SENSITO_DENSITY_RGB[:, -1] - module.SENSITO_DMIN_RGB
        )
        capacity = (
            net_capacity[:, None]
            * module.SUBEMULSION_CAPACITY_FRACTIONS[None, :]
        )
        expected = np.zeros_like(departure)
        for source_record in range(3):
            for source_population in range(3):
                sigma = max(
                    float(module.DIR_POPULATION_LATERAL_SIGMA_PX_5760[
                        source_population
                    ]),
                    0.20,
                )
                diffused = __import__("cv2").GaussianBlur(
                    departure[..., source_record, source_population],
                    (0, 0),
                    sigma,
                    borderType=__import__("cv2").BORDER_REFLECT,
                )
                for destination_record in range(3):
                    record_transport = module.DIR_INTERIMAGE_RECEIVER_CAUSER[
                        destination_record, source_record
                    ]
                    if record_transport <= 0.0:
                        continue
                    for destination_population in range(3):
                        scale = (
                            module.DIR_DEVELOPMENT_INTERIMAGE_STRENGTH
                            * record_transport
                            * module.DIR_POPULATION_TRANSPORT[
                                destination_population, source_population
                            ]
                            * module.DIR_POPULATION_RELEASE_GAIN[source_population]
                            * module.DIR_POPULATION_RECEIVER_GAIN[
                                destination_population
                            ]
                            * capacity[
                                destination_record, destination_population
                            ]
                        )
                        expected[
                            ..., destination_record, destination_population
                        ] -= (
                            scale
                            * marginal[
                                ..., destination_record, destination_population
                            ]
                            * diffused
                        )
        actual = wavefront_tile_lab_v020.mean_dir_batch(
            module,
            departure.copy(),
            marginal,
            capacity,
            1.0,
        )
        difference = np.abs(actual - expected)
        self.assertLess(float(difference.max()), 5e-9)
        self.assertLess(
            float(np.sqrt(np.mean(difference.astype(np.float64) ** 2))),
            5e-10,
        )


if __name__ == "__main__":
    unittest.main()
