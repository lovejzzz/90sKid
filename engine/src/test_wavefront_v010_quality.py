from __future__ import annotations

import unittest

import numpy as np

from audit_wavefront_v010_quality import compare_metrics, sequence_metrics


class WavefrontV010QualityTests(unittest.TestCase):
    def test_identical_sequence_has_identity_ratios_and_zero_deltas(self) -> None:
        rng = np.random.default_rng(5279)
        sequence = rng.normal(size=(3, 48, 64, 3)).astype(np.float32)
        metrics = sequence_metrics(sequence)
        comparison = compare_metrics(metrics, metrics)
        np.testing.assert_array_equal(
            comparison["spatial_rms_ratio_records"],
            np.ones(3),
        )
        np.testing.assert_array_equal(
            comparison["temporal_difference_rms_ratio_records"],
            np.ones(3),
        )
        self.assertEqual(
            comparison["maximum_absolute_normalized_nps_band_delta"],
            0.0,
        )
        self.assertEqual(
            comparison[
                "maximum_absolute_temporal_lag1_correlation_delta"
            ],
            0.0,
        )

    def test_uniform_scale_is_reported_in_energy_and_tails(self) -> None:
        rng = np.random.default_rng(43)
        reference = rng.normal(size=(3, 48, 64, 3)).astype(np.float32)
        candidate = reference * np.float32(1.01)
        comparison = compare_metrics(
            sequence_metrics(reference),
            sequence_metrics(candidate),
        )
        np.testing.assert_allclose(
            comparison["spatial_rms_ratio_records"],
            np.full(3, 1.01),
            rtol=5.0e-6,
        )
        np.testing.assert_allclose(
            comparison["temporal_difference_rms_ratio_records"],
            np.full(3, 1.01),
            rtol=5.0e-6,
        )
        self.assertLess(
            comparison["maximum_absolute_normalized_nps_band_delta"],
            1.0e-7,
        )


if __name__ == "__main__":
    unittest.main()
