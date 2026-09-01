"""Engine regression tests: run with ``python3 -m pytest studio/tests`` or directly."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from film5279 import FilmParams, decode_to_scene_linear, render_frame  # noqa: E402
from film5279 import negative as N  # noqa: E402
from film5279 import priors, spectral  # noqa: E402
from film5279.colour import TRANSFER_DECODERS, luma  # noqa: E402
from film5279.observers import observers  # noqa: E402


def test_transfer_functions_map_gray():
    assert abs(TRANSFER_DECODERS["vlog"](np.float32(0.423)) - 0.18) < 0.002
    assert abs(TRANSFER_DECODERS["slog3"](np.float32(420 / 1023)) - 0.18) < 0.002
    assert abs(TRANSFER_DECODERS["logc3"](np.float32(0.391)) - 0.18) < 0.003
    assert abs(TRANSFER_DECODERS["srgb"](np.float32(0.5)) - 0.214) < 0.002
    assert abs(TRANSFER_DECODERS["bt1886"](np.float32(0.5)) - 0.1895) < 0.002


def test_status_m_inverse_roundtrip():
    rng = np.random.default_rng(3)
    cmy = rng.uniform(0.0, 2.0, (2000, 3)).astype(np.float32)
    net = spectral.status_m_net_density_from_cmy(cmy)
    back = spectral.solve_cmy_from_status_m_fast(net)
    assert np.abs(spectral.status_m_net_density_from_cmy(back) - net).max() < 1e-4


def test_dense_lattice_matches_direct_on_physical_probes():
    model = spectral.spectral_model()
    le = np.repeat(np.linspace(-4.0, 0.0, 81, dtype=np.float32)[:, None], 3, axis=1)
    net = np.maximum(N.hd_density(le) - priors.SENSITO_DMIN_RGB, 0.0)
    sigma = N.granularity_sigma(le)
    cloud = np.concatenate([net, np.maximum(net + sigma, 0.0), np.maximum(net - sigma, 0.0)])
    direct = spectral.printer_density_direct(cloud)
    sampled = model.printer.sample(cloud)
    assert np.abs(sampled - direct).max() < 1e-3


def test_neutral_scene_stays_neutral_and_monotone():
    obs = observers()
    levels = 0.18 * np.power(2.0, np.linspace(-6.0, 5.0, 45, dtype=np.float32))
    scene = np.repeat(np.repeat(levels[None, :, None], 3, axis=2), 4, axis=0).astype(np.float32)
    params = FilmParams(grain_amount=0.0, sensor_noise_separation=False, halation=0.0)
    result = render_frame(scene, 0, params, want=("projection", "scan"), obs=obs)
    for view in (result.projection, result.scan):
        row = view[2]
        y = luma(row)
        assert np.all(np.diff(y) >= -1e-5)
        chroma = (np.max(row, axis=-1) - np.min(row, axis=-1)) / np.maximum(np.max(row, axis=-1), 1e-4)
        assert chroma[y > 0.01].max() < 0.02


def test_grain_calibration_matches_kodak_rms():
    """A uniform patch integrated over 48 um must reproduce the published sigma."""
    width = 1024
    gate = 24.89
    scale = N.native_scale_for(width, gate)
    le = np.full((256, width, 3), -2.0, dtype=np.float32)
    act = N.activation_probabilities(le)
    deviation = N.form_grain_deviation(le, act, 0, scale, width / gate, 1.0, 5, 0, 1)
    import cv2

    radius = 0.5 * 48e-3 * width / gate
    kernel = N.disk_kernel(radius)
    kernel /= kernel.sum()
    target = N.granularity_sigma(le)[0, 0]
    for c in range(3):
        integrated = cv2.filter2D(deviation[..., c], -1, kernel, borderType=cv2.BORDER_REFLECT)
        measured = integrated[8:-8, 8:-8].std()
        assert abs(measured / target[c] - 1.0) < 0.25, (c, measured, target[c])


def test_common_density_is_shared_by_records():
    mean = np.full((4, 4, 3), 1.0, dtype=np.float32)
    formed = mean + np.random.default_rng(0).normal(0, 0.01, mean.shape).astype(np.float32)
    sigma = np.full_like(mean, 0.01)
    common = N.common_density_projection(mean, formed, sigma) - mean
    assert np.allclose(common[..., 0], common[..., 1]) and np.allclose(common[..., 1], common[..., 2])


def test_render_frame_end_to_end_shapes():
    encoded = np.random.default_rng(1).uniform(0.0, 1.0, (72, 128, 3)).astype(np.float32)
    params = FilmParams()
    scene = decode_to_scene_linear(encoded, params)
    result = render_frame(scene, 5, params, want=("projection", "scan", "negative", "cineon"))
    assert result.projection.shape == scene.shape and result.scan.shape == scene.shape
    assert result.cineon_code.dtype == np.uint16 and result.cineon_code.max() <= 1023
    assert np.isfinite(result.projection).all() and np.isfinite(result.scan).all()


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_"):
            function()
            print("ok", name)
