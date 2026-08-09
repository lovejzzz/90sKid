#!/usr/bin/env python3
"""Deterministic unit tests for V32 colour and OFX-region kernels."""

from __future__ import annotations

import unittest

import numpy as np

import emulsion_experiment as e
from apply_v31_normal_process_adapter import adapt_frame
from build_v32_dcdm_reference import encode_dcdm_xyz
from validate_v32_measurement import adapt_frame_tiled, decode_dcdm_xyz


class V32KernelTests(unittest.TestCase):
    def test_dcdm_12bit_xyz_roundtrip(self) -> None:
        rng = np.random.default_rng(5279)
        linear = rng.uniform(0.02, 0.82, (64, 96, 3)).astype(np.float32)
        stored_rgb = encode_dcdm_xyz(linear)
        recovered = decode_dcdm_xyz(stored_rgb[..., ::-1])
        self.assertTrue(bool(np.all(np.bitwise_and(stored_rgb, 15) == 0)))
        self.assertLess(float(np.percentile(np.abs(recovered - linear), 99)), 0.003)

    def test_ofx_roi_matches_full_frame(self) -> None:
        rng = np.random.default_rng(2383)
        projection = rng.uniform(0.02, 0.98, (360, 480, 3)).astype(np.float32)
        scan = np.clip(
            projection * np.asarray([1.01, 0.995, 0.985], dtype=np.float32),
            0.0,
            1.0,
        )
        full = adapt_frame(projection, scan)
        tiled, contract = adapt_frame_tiled(projection, scan, tile=128)
        delta = np.abs(full - tiled)
        self.assertEqual(contract["halo"], 2)
        self.assertLess(float(np.percentile(delta, 99)), 5e-4)


if __name__ == "__main__":
    unittest.main()
