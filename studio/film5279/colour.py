"""Transfer functions, primaries and perceptual helpers for the 5279 studio.

Everything here is deterministic colour arithmetic.  Film formation lives in
``negative.py``; the two material observers live in ``observers.py``.
"""

from __future__ import annotations

import numpy as np

from . import priors

LUMA_709 = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


# ---------------------------------------------------------------------------
# Transfer functions (encoded signal -> scene or display linear)
# ---------------------------------------------------------------------------


def srgb_decode(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32)
    return np.where(v <= 0.04045, v / 12.92, np.power((np.abs(v) + 0.055) / 1.055, 2.4)).astype(np.float32)


def srgb_encode(linear: np.ndarray) -> np.ndarray:
    l = np.clip(np.asarray(linear, dtype=np.float32), 0.0, 1.0)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * np.power(l, 1.0 / 2.4) - 0.055).astype(np.float32)


def bt709_oetf_decode(v: np.ndarray) -> np.ndarray:
    """Inverse of the BT.709 camera OETF (scene-referred interpretation)."""
    v = np.asarray(v, dtype=np.float32)
    return np.where(v < 0.081, v / 4.5, np.power((np.abs(v) + 0.099) / 1.099, 1.0 / 0.45)).astype(np.float32)


def bt1886_decode(v: np.ndarray) -> np.ndarray:
    return np.power(np.clip(np.asarray(v, dtype=np.float32), 0.0, None), 2.4).astype(np.float32)


def bt1886_encode(linear: np.ndarray) -> np.ndarray:
    return np.power(np.clip(np.asarray(linear, dtype=np.float32), 0.0, 1.0), 1.0 / 2.4).astype(np.float32)


def gamma22_decode(v: np.ndarray) -> np.ndarray:
    return np.power(np.clip(np.asarray(v, dtype=np.float32), 0.0, None), 2.2).astype(np.float32)


def vlog_decode(v: np.ndarray) -> np.ndarray:
    """Panasonic V-Log to reflectance-linear (18% gray -> 0.18)."""
    v = np.asarray(v, dtype=np.float32)
    b, c, d = 0.00873, 0.241514, 0.598
    return np.where(v < 0.181, (v - 0.125) / 5.6, np.power(10.0, (v - d) / c) - b).astype(np.float32)


def slog3_decode(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32)
    code = v * 1023.0
    linear = np.where(
        code >= 171.2102946929,
        (np.power(10.0, (code - 420.0) / 261.5)) * (0.18 + 0.01) - 0.01,
        (code - 95.0) * 0.01125 / (171.2102946929 - 95.0),
    )
    return linear.astype(np.float32)


def logc3_decode(v: np.ndarray) -> np.ndarray:
    """ARRI LogC (v3, EI 800) to scene-linear."""
    v = np.asarray(v, dtype=np.float32)
    cut, a, b, c, d, e, f = 0.010591, 5.555556, 0.052272, 0.247190, 0.385537, 5.367655, 0.092809
    return np.where(v > e * cut + f, (np.power(10.0, (v - d) / c) - b) / a, (v - f) / e).astype(np.float32)


def hlg_decode(v: np.ndarray) -> np.ndarray:
    """HLG inverse OETF, scaled so 75% signal (reference white) is 1.0."""
    v = np.asarray(v, dtype=np.float32)
    a, b, c = 0.17883277, 0.28466892, 0.55991073
    energy = np.where(v <= 0.5, np.square(v) / 3.0, (np.exp((v - c) / a) + b) / 12.0)
    white = (np.exp((0.75 - c) / a) + b) / 12.0
    return (energy / white).astype(np.float32)


def pq_decode(v: np.ndarray) -> np.ndarray:
    """ST 2084 inverse EOTF, scaled so 203 nit reference white is 1.0."""
    v = np.clip(np.asarray(v, dtype=np.float32), 0.0, 1.0)
    m1, m2, c1, c2, c3 = 0.1593017578125, 78.84375, 0.8359375, 18.8515625, 18.6875
    p = np.power(v, 1.0 / m2)
    nits = 10000.0 * np.power(np.maximum(p - c1, 0.0) / (c2 - c3 * p), 1.0 / m1)
    return (nits / 203.0).astype(np.float32)


TRANSFER_DECODERS = {
    "bt709": bt709_oetf_decode,
    "bt1886": bt1886_decode,
    "srgb": srgb_decode,
    "gamma22": gamma22_decode,
    "vlog": vlog_decode,
    "slog3": slog3_decode,
    "logc3": logc3_decode,
    "hlg": hlg_decode,
    "pq": pq_decode,
    "linear": lambda v: np.asarray(v, dtype=np.float32),
}

TRANSFER_LABELS = {
    "bt709": "Rec.709 camera OETF",
    "bt1886": "Rec.709 display (BT.1886 γ2.4)",
    "srgb": "sRGB",
    "gamma22": "Gamma 2.2",
    "vlog": "Panasonic V-Log",
    "slog3": "Sony S-Log3",
    "logc3": "ARRI LogC3 (EI 800)",
    "hlg": "HLG",
    "pq": "PQ / ST 2084",
    "linear": "Linear",
}


# ---------------------------------------------------------------------------
# Primaries (source gamut -> linear Rec.709, the virtual stock's input basis)
# ---------------------------------------------------------------------------

XYZ_D65_TO_REC709 = np.asarray(priors.XYZ_D65_TO_REC709, dtype=np.float64)
REC709_TO_XYZ_D65 = np.asarray(priors.REC709_TO_XYZ_D65, dtype=np.float64)
BT2020_TO_XYZ_D65 = np.asarray(priors.BT2020_TO_XYZ_D65, dtype=np.float64)
P3D65_TO_XYZ = np.array(
    [[0.486571, 0.265668, 0.198217], [0.228975, 0.691739, 0.079287], [0.0, 0.045113, 1.043944]]
)
VGAMUT_TO_XYZ = np.asarray(priors.VGAMUT_TO_XYZ_D65, dtype=np.float64)
SGAMUT3CINE_TO_XYZ = np.array(
    [[0.5990839, 0.2489255, 0.1024464], [0.2150758, 0.8850685, -0.1001443], [-0.0320658, -0.0276583, 1.1487819]]
)
ALEXA_WIDE_TO_XYZ = np.array(
    [[0.638008, 0.214704, 0.097744], [0.291954, 0.823841, -0.115795], [0.002798, -0.067034, 1.153294]]
)

GAMUT_TO_XYZ = {
    "rec709": REC709_TO_XYZ_D65,
    "bt2020": BT2020_TO_XYZ_D65,
    "p3d65": P3D65_TO_XYZ,
    "vgamut": VGAMUT_TO_XYZ,
    "sgamut3cine": SGAMUT3CINE_TO_XYZ,
    "alexawide": ALEXA_WIDE_TO_XYZ,
}

GAMUT_LABELS = {
    "rec709": "Rec.709 / sRGB",
    "bt2020": "Rec.2020",
    "p3d65": "P3-D65",
    "vgamut": "Panasonic V-Gamut",
    "sgamut3cine": "Sony S-Gamut3.Cine",
    "alexawide": "ARRI Wide Gamut 3",
}


def gamut_to_rec709_matrix(gamut: str) -> np.ndarray:
    if gamut == "rec709":
        return np.eye(3, dtype=np.float32)
    return (XYZ_D65_TO_REC709 @ GAMUT_TO_XYZ[gamut]).astype(np.float32)


def apply_matrix(image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return np.einsum("...c,dc->...d", np.asarray(image, dtype=np.float32), np.asarray(matrix, dtype=np.float32)).astype(np.float32)


# ---------------------------------------------------------------------------
# Perceptual helpers (identical to the research engine)
# ---------------------------------------------------------------------------

_RGB_TO_LMS = np.array(
    [[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]],
    dtype=np.float32,
)
_LMS_TO_LAB = np.array(
    [[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]],
    dtype=np.float32,
)
_LAB_TO_LMS_ROOT = np.array(
    [[1.0, 0.3963377774, 0.2158037573], [1.0, -0.1055613458, -0.0638541728], [1.0, -0.0894841775, -1.2914855480]],
    dtype=np.float32,
)
_LMS_TO_RGB = np.array(
    [[4.0767416621, -3.3077115913, 0.2309699292], [-1.2684380046, 2.6097574011, -0.3413193965], [-0.0041960863, -0.7034186147, 1.7076147010]],
    dtype=np.float32,
)


def linear_rec709_to_oklab(rgb: np.ndarray) -> np.ndarray:
    lms = np.einsum("...c,dc->...d", np.maximum(rgb, 0.0), _RGB_TO_LMS)
    return np.einsum("...c,dc->...d", np.cbrt(np.maximum(lms, 0.0)), _LMS_TO_LAB).astype(np.float32)


def oklab_to_linear_rec709(lab: np.ndarray) -> np.ndarray:
    root = np.einsum("...c,dc->...d", lab, _LAB_TO_LMS_ROOT)
    return np.einsum("...c,dc->...d", root**3, _LMS_TO_RGB).astype(np.float32)


def compress_oklab_chroma_to_rec709(rgb: np.ndarray, lower_bound: float = 0.0) -> np.ndarray:
    """Fit extended RGB into Rec.709 while preserving OKLab lightness and hue."""
    source = np.asarray(rgb, dtype=np.float32)
    result = source.copy()
    out = np.any((source < lower_bound) | (source > 1.0), axis=-1)
    if not np.any(out):
        return result
    extended = source[out]
    lab = linear_rec709_to_oklab(extended)
    lab[:, 0] = np.clip(lab[:, 0], 0.0, 1.0)
    low = np.zeros(lab.shape[0], dtype=np.float32)
    high = np.ones(lab.shape[0], dtype=np.float32)
    for _ in range(8):
        scale = 0.5 * (low + high)
        candidate_lab = lab.copy()
        candidate_lab[:, 1:3] *= scale[:, None]
        candidate = oklab_to_linear_rec709(candidate_lab)
        fits = np.all((candidate >= lower_bound) & (candidate <= 1.0), axis=1)
        low = np.where(fits, scale, low)
        high = np.where(fits, high, scale)
    lab[:, 1:3] *= low[:, None]
    result[out] = oklab_to_linear_rec709(lab)
    np.clip(result, lower_bound, 1.0, out=result)
    return result


def compress_unit_gamut(rgb: np.ndarray) -> np.ndarray:
    """Compress only out-of-range chroma around Rec.709 luminance."""
    luma = np.clip(np.einsum("...c,c->...", rgb, LUMA_709), 0.0, 1.0)
    chroma = rgb - luma[..., None]
    upper = np.max(chroma, axis=-1)
    lower = -np.min(chroma, axis=-1)
    upper_scale = np.where(upper > 1e-6, (1.0 - luma) / np.maximum(upper, 1e-6), 1.0)
    lower_scale = np.where(lower > 1e-6, luma / np.maximum(lower, 1e-6), 1.0)
    scale = np.minimum(1.0, np.minimum(upper_scale, lower_scale))
    return np.clip(luma[..., None] + chroma * scale[..., None], 0.0, 1.0).astype(np.float32)


def smoothstep(edge0: float, edge1: float, value: np.ndarray) -> np.ndarray:
    t = np.clip((np.asarray(value, dtype=np.float32) - edge0) / (edge1 - edge0), 0.0, 1.0)
    return (t * t * (3.0 - 2.0 * t)).astype(np.float32)


def luma(rgb: np.ndarray) -> np.ndarray:
    return np.einsum("...c,c->...", np.asarray(rgb, dtype=np.float32), LUMA_709).astype(np.float32)
