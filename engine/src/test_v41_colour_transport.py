from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v40_profile
import v41_profile


ROOT = Path(__file__).resolve().parents[1]
AUDIT = (
    ROOT
    / "research_runs/2026-08-06_t003_colorchecker/frame160_audit"
    / "t003_dkc_pro_audit.json"
)


class V41ColourTransportTests(unittest.TestCase):
    def test_v41_preserves_d65_neutral_axis_and_luminance(self) -> None:
        v41_profile.apply(e)
        levels = np.geomspace(1e-4, 8.0, 64, dtype=np.float32)
        neutral = np.repeat(levels[:, None], 3, axis=1)
        corrected = e.apply_input_chroma_residual(neutral)
        np.testing.assert_allclose(corrected, neutral, rtol=3e-5, atol=3e-6)

        rng = np.random.default_rng(41)
        source = rng.uniform(0.0, 4.0, size=(128, 3)).astype(np.float32)
        corrected = e.apply_input_chroma_residual(source)
        before_y = source @ e.BT2020_TO_XYZ_D65[1]
        after_y = corrected @ e.BT2020_TO_XYZ_D65[1]
        np.testing.assert_allclose(after_y, before_y, rtol=4e-5, atol=4e-6)

    def test_v41_uses_signed_basis_only_for_nonnegative_records(self) -> None:
        report = json.loads(AUDIT.read_text(encoding="utf-8"))
        cyan = np.asarray(
            report["patches"][9]["decoded_linear_bt2020_median"], dtype=np.float32
        )
        v41_profile.apply(e)
        film = e.bt2020_to_balanced_film_rgb(cyan * (2.0**0.45))
        self.assertLess(float(film[0]), 0.0)
        signed = film @ e.FILM_RECORD_SENSITIVITY_RGB.T
        self.assertTrue(np.all(signed >= 0.0))
        np.testing.assert_allclose(e.film_records_from_rgb(film), signed, rtol=1e-6)

        unsafe = np.asarray([-1.0, 0.01, 0.01], dtype=np.float32)
        self.assertTrue(np.any(unsafe @ e.FILM_RECORD_SENSITIVITY_RGB.T < 0.0))
        expected = np.maximum(unsafe, 0.0) @ e.FILM_RECORD_SENSITIVITY_RGB.T
        np.testing.assert_allclose(e.film_records_from_rgb(unsafe), expected, rtol=1e-6)

    def test_v40_archive_boundary_is_unchanged(self) -> None:
        v40_profile.apply(e)
        source = np.asarray([-0.1, 0.5, 0.7], dtype=np.float32)
        clipped = np.maximum(source, 0.0)
        np.testing.assert_allclose(
            e.film_records_from_rgb(clipped),
            clipped @ e.FILM_RECORD_SENSITIVITY_RGB.T,
            rtol=1e-6,
        )


if __name__ == "__main__":
    unittest.main()
