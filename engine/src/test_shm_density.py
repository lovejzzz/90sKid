#!/usr/bin/env python3
"""Invariant and morphology tests for the SHM experimental comparator."""

from __future__ import annotations

import unittest
import json
from pathlib import Path

import numpy as np

from fsd_density import _srgb_encode
from shm_density import (
    DEFAULT_PROFILE,
    SHM_LUMA,
    apply_shm,
    morphology_latent_field,
    morphology_uniform_field,
    trix_reference_tone_gain,
)
from fsd_density import (
    _lookup_binomial_density,
    binomial_quantile_table,
    tone_taper,
)


def lag1(field: np.ndarray) -> tuple[float, float]:
    centered = field - field.mean()
    variance = float(np.mean(centered * centered))
    return (
        float(np.mean(centered[:, :-1] * centered[:, 1:]) / variance),
        float(np.mean(centered[:-1] * centered[1:]) / variance),
    )


class SHMDensityTests(unittest.TestCase):
    def test_field_is_non_gaussian_isotropic_and_in_measured_envelope(self) -> None:
        field = morphology_latent_field(1024, 1024, 12)
        x1, y1 = lag1(field)
        centered = field - field.mean()
        variance = float(np.mean(centered * centered))
        skew = float(np.mean(centered**3) / variance**1.5)
        kurtosis = float(np.mean(centered**4) / variance**2 - 3.0)
        self.assertLess(abs(x1 - y1), 0.035)
        self.assertGreater((x1 + y1) * 0.5, 0.24)
        self.assertLess((x1 + y1) * 0.5, 0.46)
        self.assertGreater(skew, 0.025)
        self.assertLess(skew, 0.22)
        self.assertGreater(kurtosis, -0.30)
        self.assertLess(kurtosis, 0.70)

    def test_tone_does_not_breathe_the_reference_stock(self) -> None:
        shadow = morphology_latent_field(1024, 1024, 17, tone=0.08)
        middle = morphology_latent_field(1024, 1024, 17, tone=0.50)
        highlight = morphology_latent_field(1024, 1024, 17, tone=0.92)
        s_lag = sum(lag1(shadow)) * 0.5
        m_lag = sum(lag1(middle)) * 0.5
        h_lag = sum(lag1(highlight)) * 0.5
        self.assertLess(max(s_lag, m_lag, h_lag) - min(s_lag, m_lag, h_lag), 0.03)
        for field in (shadow, middle, highlight):
            self.assertAlmostEqual(float(field.mean()), 0.0, places=5)
            self.assertAlmostEqual(float(field.std()), 1.0, places=5)

    def test_controlled_trix_midscale_rms(self) -> None:
        # Black-box target at code 0.53167 is 0.0143094 in the same 16-bit
        # signal domain. This protects the regression from the former coarse,
        # roughly two-times-too-strong N=176 experiment.
        encoded = np.full((1024, 1024, 3), 0.5316701, dtype=np.float32)
        from fsd_density import _srgb_decode
        out, _ = apply_shm(_srgb_decode(encoded), 17)
        residual = _srgb_encode(out)[..., 0] - encoded[..., 0]
        self.assertLess(abs(float(residual.std()) - 0.0143094), 0.00075)

    def test_controlled_trix_organization_not_only_rms(self) -> None:
        """Protect correlation and thick tails from a Gaussian regression."""
        report_path = (
            Path(__file__).resolve().parents[1]
            / "research_runs/v47_silver_efex_trix_blackbox.json"
        )
        target = json.loads(report_path.read_text())["flat_fields"][8]
        tone = np.full((1024, 1024), target["source_signal"], dtype=np.float32)
        uniform = morphology_uniform_field(
            1024, 1024, 1208, DEFAULT_PROFILE, tone
        )
        candidate = _lookup_binomial_density(
            tone, uniform, binomial_quantile_table(DEFAULT_PROFILE.site_count)
        )
        residual = (
            tone_taper(tone)
            * trix_reference_tone_gain(tone)
            * (candidate - tone)
        ).astype(np.float64)
        residual -= residual.mean()
        variance = float(np.mean(residual * residual))
        x1 = float(np.mean(residual[:, :-1] * residual[:, 1:]) / variance)
        y1 = float(np.mean(residual[:-1] * residual[1:]) / variance)
        skew = float(np.mean(residual**3) / variance**1.5)
        kurtosis = float(np.mean(residual**4) / variance**2 - 3.0)
        self.assertLess(abs((x1 + y1) * 0.5 - target["lag1_mean"]), 0.018)
        self.assertLess(abs(skew - target["skew"]), 0.075)
        self.assertGreater(kurtosis, 0.18)
        self.assertLess(kurtosis, 0.48)

    def test_frame_identity_renews_morphology(self) -> None:
        a = morphology_latent_field(256, 320, 50)
        b = morphology_latent_field(256, 320, 51)
        self.assertLess(abs(float(np.corrcoef(a.ravel(), b.ravel())[0, 1])), 0.02)

    def test_density_changes_luma_not_opponent_field(self) -> None:
        yy, xx = np.mgrid[:96, :128].astype(np.float32)
        base = 0.015 + 0.7 * xx / 127.0 * (0.5 + 0.5 * yy / 95.0)
        rgb = np.stack([base, np.minimum(base * 0.8, 1), base * 0.35], axis=-1)
        out, stats = apply_shm(rgb, 12)
        src = _srgb_encode(rgb)
        dst = _srgb_encode(out)
        sy = np.einsum("...c,c->...", src, SHM_LUMA)
        dy = np.einsum("...c,c->...", dst, SHM_LUMA)
        np.testing.assert_allclose(dst - dy[..., None], src - sy[..., None], atol=4e-6)
        self.assertEqual(stats["pipeline"], "Silver-Halide Morphology (SHM)")
        self.assertTrue(np.all(np.isfinite(out)))


if __name__ == "__main__":
    unittest.main()
