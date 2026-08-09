#!/usr/bin/env python3
"""Small invariant tests for the independent FSD control."""

from __future__ import annotations

import unittest

import numpy as np

from fsd_density import (
    LUMA,
    _srgb_encode,
    _transport_luma_without_chroma_modulation,
    apply_fsd,
)


class FSDDensityTests(unittest.TestCase):
    def test_transport_changes_signal_luma_not_opponent_field(self) -> None:
        rgb = np.asarray(
            [[[0.31, 0.15, 0.002], [0.02, 0.08, 0.01], [0.94, 0.72, 0.13]]],
            dtype=np.float32,
        )
        luma = np.einsum("...c,c->...", rgb, LUMA)
        requested = np.asarray([[0.02, 0.25, 0.98]], dtype=np.float32)
        output, constrained = _transport_luma_without_chroma_modulation(
            rgb, luma, requested
        )
        source_opponent = rgb - luma[..., None]
        output_luma = np.einsum("...c,c->...", output, LUMA)
        output_opponent = output - output_luma[..., None]
        np.testing.assert_allclose(output_opponent, source_opponent, atol=2e-7)
        self.assertGreater(constrained, 0.0)
        self.assertTrue(np.all(output >= 0.0))
        self.assertTrue(np.all(output <= 1.0))

    def test_apply_fsd_has_no_independent_signal_opponent_impulses(self) -> None:
        yy, xx = np.mgrid[:48, :64].astype(np.float32)
        base = 0.01 + 0.65 * (xx / 63.0) * (0.4 + 0.6 * yy / 47.0)
        rgb = np.stack(
            [np.minimum(base * 1.35, 1.0), base, base * 0.32], axis=-1
        ).astype(np.float32)
        output, stats = apply_fsd(
            rgb,
            17,
            site_count=176,
            correlation_sigma=0.597,
        )
        source_signal = _srgb_encode(rgb)
        output_signal = _srgb_encode(output)
        source_luma = np.einsum("...c,c->...", source_signal, LUMA)
        output_luma = np.einsum("...c,c->...", output_signal, LUMA)
        source_opponent = source_signal - source_luma[..., None]
        output_opponent = output_signal - output_luma[..., None]
        np.testing.assert_allclose(output_opponent, source_opponent, atol=3e-6)
        self.assertEqual(
            stats["density_domain"],
            "IEC 61966-2-1 signal after the deterministic observer",
        )
        self.assertTrue(np.all(np.isfinite(output)))
        self.assertTrue(np.all(output >= 0.0))
        self.assertTrue(np.all(output <= 1.0))

    def test_absolute_frame_changes_the_realization(self) -> None:
        rgb = np.full((48, 64, 3), 0.18, dtype=np.float32)
        a, _ = apply_fsd(rgb, 100, site_count=176, correlation_sigma=0.597)
        b, _ = apply_fsd(rgb, 101, site_count=176, correlation_sigma=0.597)
        self.assertFalse(np.array_equal(a, b))


if __name__ == "__main__":
    unittest.main()
