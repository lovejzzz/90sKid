"""Spectral colour chain: 5279 Status-M inverse, 2383 printing and projection.

The chain reproduces the research engine's V61/V62/V63/V64/V66 equations:

    Status-M net record density
      -> joint nonnegative analytical C/M/Y dye amounts (Kodak 5279 spectra)
      -> spectral transmission incl. the coloured-coupler mask (D-min spectrum)
      -> 3200 K printer light integrated through the 2383 record sensitivities
      -> 2383 separated Status-A H-D curves with LAD printer lights
      -> analytical 2383 dye amounts, D-min-registered base spectrum
      -> xenon projector x CIE 1931 2deg (1 nm) -> XYZ -> Rec.709 linear

Two dense lattices replace the historical 29-cube / 25-cube caches.  Their
sizes follow the V87 gate audit.  Both lattices are built from the direct
evaluation on first use and cached on disk.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import threading

import numpy as np

from . import fast, priors

CACHE_ROOT = Path(os.environ.get("FILM5279_CACHE", Path(__file__).resolve().parents[1] / "cache"))
_CIE_PATH = Path(__file__).resolve().parent / "cie_xyz_1931_2deg_1nm.csv"
_LOCK = threading.Lock()

MAX_RECORD_DENSITY = float(priors.NEGATIVE_5279_MAX_RECORD_DENSITY)
PRINT_DMAX = float(priors.PRINT_2383_DMAX)


def priors_fingerprint() -> str:
    return hashlib.sha256(Path(priors.__file__).read_bytes()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 5279: Status-M <-> analytical CMY
# ---------------------------------------------------------------------------


def _status_m_model():
    weights = np.asarray(priors.NEGATIVE_5279_STATUS_M_RGB_WEIGHTS, dtype=np.float64)
    wavelengths = np.asarray(priors.NEGATIVE_5279_STATUS_M_WAVELENGTHS_NM, dtype=np.float32)
    dmin = np.interp(wavelengths, priors.NEGATIVE_DYE_WAVELENGTHS_NM, priors.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY).astype(np.float32).astype(np.float64)
    spectra = np.column_stack(
        [
            np.interp(wavelengths, priors.NEGATIVE_DYE_WAVELENGTHS_NM, priors.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY[:, c])
            for c in range(3)
        ]
    ).astype(np.float32).astype(np.float64)
    base_density = -np.log10(np.maximum(np.power(10.0, -dmin) @ weights, 1e-30))
    return weights, dmin, spectra, base_density


_STATUS_M = _status_m_model()


def status_m_net_density_from_cmy(cmy: np.ndarray) -> np.ndarray:
    weights, dmin, spectra, base_density = _STATUS_M
    flat = np.asarray(cmy, dtype=np.float64).reshape(-1, 3)
    with np.errstate(all="ignore"):
        transmission = np.power(10.0, -(dmin[None, :] + flat @ spectra.T))
        density = -np.log10(np.maximum(transmission @ weights, 1e-30))
    return (density - base_density).reshape(np.asarray(cmy).shape).astype(np.float32)


def solve_cmy_from_status_m(status_m_net_density: np.ndarray, iterations: int = 24) -> np.ndarray:
    """Bounded projected Gauss-Newton joint inverse (V61), identical to the engine."""
    weights, dmin, spectra, base_density = _STATUS_M
    source = np.asarray(status_m_net_density, dtype=np.float64)
    target = np.maximum(source.reshape(-1, 3), 0.0)

    def forward_and_jacobian(coefficients):
        with np.errstate(all="ignore"):
            transmission = np.power(10.0, -(dmin[None, :] + coefficients @ spectra.T))
            integrated = np.maximum(transmission @ weights, 1e-30)
            density = -np.log10(integrated) - base_density
            # Same quantity as einsum("nl,lj,lk->njk") but as three BLAS products.
            jacobian = np.empty((transmission.shape[0], 3, 3), dtype=np.float64)
            for j in range(3):
                jacobian[:, j, :] = ((transmission * weights[None, :, j]) @ spectra) / integrated[:, j : j + 1]
        return density, jacobian

    _, origin_jacobian = forward_and_jacobian(np.zeros((1, 3)))
    with np.errstate(all="ignore"):
        coefficients = np.maximum(target @ np.linalg.inv(origin_jacobian[0]).T, 0.0)
    diagonal = np.arange(3)
    for _ in range(iterations):
        density, jacobian = forward_and_jacobian(coefficients)
        residual = density - target
        normal = np.einsum("nji,njk->nik", jacobian, jacobian)
        gradient = np.einsum("nji,nj->ni", jacobian, residual)
        normal[:, diagonal, diagonal] += 1e-8
        step = -np.linalg.solve(normal, gradient[..., None])[..., 0]
        damping = np.maximum(1.0, np.max(np.abs(step), axis=1, keepdims=True) / 0.5)
        coefficients = np.clip(coefficients + step / damping, 0.0, 12.0)
    return coefficients.reshape(source.shape).astype(np.float32)


# ---------------------------------------------------------------------------
# 5279 -> 2383 printer density (direct)
# ---------------------------------------------------------------------------


def blackbody_spd(wavelength_nm: np.ndarray, temperature_k: float) -> np.ndarray:
    wl = np.asarray(wavelength_nm, dtype=np.float64) * 1e-9
    c2 = 1.438776877e-2
    spd = 1.0 / (np.power(wl, 5.0) * np.expm1(c2 / (wl * temperature_k)))
    return (spd / np.max(spd)).astype(np.float32)


def _printer_weights() -> np.ndarray:
    lamp = blackbody_spd(priors.NEGATIVE_DYE_WAVELENGTHS_NM, 3200.0).astype(np.float64)
    sensitivity = np.power(10.0, np.asarray(priors.PRINT_2383_LOG_SENSITIVITY_CMY, dtype=np.float64))
    weights = lamp[:, None] * sensitivity
    return weights / np.sum(weights, axis=0, keepdims=True)


_PRINTER_WEIGHTS = _printer_weights()


def printer_density_direct(status_m_net_density: np.ndarray, chunk: int = 65536) -> np.ndarray:
    """Exact 2383 record density seen through the formed 5279 negative."""
    source = np.asarray(status_m_net_density, dtype=np.float64)
    flat = source.reshape(-1, 3)
    spectra = np.asarray(priors.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY, dtype=np.float64)
    dmin = np.asarray(priors.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY, dtype=np.float64)
    out = np.empty_like(flat, dtype=np.float32)
    for start in range(0, flat.shape[0], chunk):
        stop = min(start + chunk, flat.shape[0])
        cmy = solve_cmy_from_status_m_fast(flat[start:stop]).astype(np.float64)
        spectral = np.clip(dmin[None, :] + cmy @ spectra.T, 0.0, 16.0)
        out[start:stop] = -np.log10(np.maximum(np.power(10.0, -spectral) @ _PRINTER_WEIGHTS, 1e-12))
    return out.reshape(source.shape)


def negative_light_table_rgb_direct(status_m_net_density: np.ndarray) -> np.ndarray:
    """What the orange-masked negative looks like on a 3200 K light table.

    Purely a preview aid: spectral transmission of D-min plus dyes under a
    tungsten lamp, integrated with the CIE observer and adapted to D65.
    """
    op = projection_operator()
    source = np.asarray(status_m_net_density, dtype=np.float64)
    flat = source.reshape(-1, 3)
    wavelengths = op["wavelengths"]
    spectra = np.stack(
        [np.interp(wavelengths, priors.NEGATIVE_DYE_WAVELENGTHS_NM, priors.NEGATIVE_5279_NET_DYE_CMY_SPECTRAL_DENSITY[:, c]) for c in range(3)],
        axis=1,
    )
    dmin = np.interp(wavelengths, priors.NEGATIVE_DYE_WAVELENGTHS_NM, priors.NEGATIVE_5279_DMIN_SPECTRAL_DENSITY)
    lamp = blackbody_spd(wavelengths, 3200.0).astype(np.float64)
    weighted = lamp[:, None] * op["cmf"] * op["trapezoid"][:, None]
    white = np.sum(weighted, axis=0)
    adaptation = bradford_to_d65(white / white[1])
    out = np.empty_like(flat, dtype=np.float32)
    for start in range(0, flat.shape[0], 65536):
        stop = min(start + 65536, flat.shape[0])
        cmy = solve_cmy_from_status_m_fast(flat[start:stop]).astype(np.float64)
        spectral = np.clip(dmin[None, :] + cmy @ spectra.T, 0.0, 16.0)
        xyz = np.power(10.0, -spectral) @ weighted / white[1]
        out[start:stop] = (xyz @ adaptation.T) @ np.asarray(priors.XYZ_D65_TO_REC709, dtype=np.float64).T
    return out.reshape(source.shape)


# ---------------------------------------------------------------------------
# 2383 print: Status-A H-D, LAD printer lights, analytical dye amounts
# ---------------------------------------------------------------------------


def _status_a_model():
    wl = np.asarray(priors.PRINT_STATUS_A_WAVELENGTHS_NM, dtype=np.float32)
    dye = np.stack(
        [np.interp(wl, priors.PRINT_DYE_WAVELENGTHS_NM, priors.PRINT_DYE_CMY_SPECTRAL_DENSITY[:, c]) for c in range(3)], axis=1
    ).astype(np.float64)
    weights = np.asarray(priors.PRINT_STATUS_A_RGB_WEIGHTS, dtype=np.float64)
    weight_sums = np.sum(weights, axis=0)
    base = np.interp(wl, priors.PRINT_DYE_WAVELENGTHS_NM, priors.PRINT_2383_DMIN_SPECTRAL_DENSITY).astype(np.float64)
    base_transmission = np.power(10.0, -np.clip(base, 0.0, 20.0))
    base_status_a = -np.log10(np.maximum(np.sum(base_transmission[:, None] * weights, axis=0) / weight_sums, 1e-12))
    return dye, weights, weight_sums, base, base_status_a


_STATUS_A = _status_a_model()
_AMOUNT_AXIS = np.linspace(0.0, 14.0, 28001, dtype=np.float64)


def _principal_density_tables() -> list[tuple[np.ndarray, np.ndarray]]:
    """Per channel: monotone principal Status-A density vs analytical dye amount."""
    dye, weights, weight_sums, base, base_status_a = _STATUS_A
    dmin = np.asarray(priors.PRINT_2383_STATUS_A_DMIN_RGB, dtype=np.float64)
    tables = []
    for c in range(3):
        spectral = _AMOUNT_AXIS[:, None] * dye[None, :, c] + base[None, :]
        transmission = np.power(10.0, -np.clip(spectral, 0.0, 20.0))
        measured = np.einsum("aw,w->a", transmission, weights[:, c])
        principal = -np.log10(np.maximum(measured / weight_sums[c], 1e-12)) - base_status_a[c] + dmin[c]
        tables.append((principal, _AMOUNT_AXIS))
    return tables


_PRINCIPAL_TABLES = _principal_density_tables()


def print_dye_amounts(status_a_density: np.ndarray) -> np.ndarray:
    """Invert each separated principal Status-A density to dye amount (V60)."""
    source = np.asarray(status_a_density, dtype=np.float64)
    out = np.empty_like(source)
    for c in range(3):
        principal, amounts = _PRINCIPAL_TABLES[c]
        out[..., c] = np.interp(source[..., c], principal, amounts)
    return out


def print_log_exposure_aim() -> np.ndarray:
    """Printer-light aim: log exposure that puts each record on its LAD principal density."""
    return np.array(
        [
            np.interp(float(priors.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB[c]), priors.PRINT_2383_DENSITY_RGB[c], priors.PRINT_2383_LOG_EXPOSURE)
            for c in range(3)
        ],
        dtype=np.float32,
    )


def print_density_from_printer_density(negative_printer_density: np.ndarray, neutral_negative_printer_density: np.ndarray) -> np.ndarray:
    """Expose 2383 through the negative with neutral LAD printer lights (V64 unshaped)."""
    aim = print_log_exposure_aim()
    printer_log_light = np.asarray(neutral_negative_printer_density, dtype=np.float32) + aim
    log_exposure = (printer_log_light - np.asarray(negative_printer_density, dtype=np.float32)).astype(np.float32)
    density = np.empty_like(log_exposure, dtype=np.float32)
    for c in range(3):
        density[..., c] = np.interp(log_exposure[..., c], priors.PRINT_2383_LOG_EXPOSURE, priors.PRINT_2383_DENSITY_RGB[c]).astype(np.float32)
    return density


def apply_callier(print_density: np.ndarray) -> np.ndarray:
    from .colour import smoothstep

    net = np.maximum(print_density - priors.PRINT_2383_DENSITY_RGB[:, 0], 0.0)
    shoulder = 1.0 - 0.65 * smoothstep(3.0, PRINT_DMAX, net)
    return (print_density + net * shoulder * priors.PRINT_2383_CALLIER_GAIN_RGB).astype(np.float32)


# ---------------------------------------------------------------------------
# Xenon projection through the CIE 1931 observer
# ---------------------------------------------------------------------------


def bradford_to_d65(source_white_xyz: np.ndarray) -> np.ndarray:
    bradford = np.array([[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]])
    d65 = np.array([0.95047, 1.0, 1.08883])
    return np.linalg.inv(bradford) @ np.diag((bradford @ d65) / np.maximum(bradford @ source_white_xyz, 1e-8)) @ bradford


_PROJECTION_OPERATOR: dict | None = None


def projection_operator() -> dict:
    global _PROJECTION_OPERATOR
    if _PROJECTION_OPERATOR is not None:
        return _PROJECTION_OPERATOR
    table = np.loadtxt(_CIE_PATH, delimiter=",", dtype=np.float64)
    selection = (table[:, 0] >= 380.0) & (table[:, 0] <= 780.0)
    wavelengths = table[selection, 0]
    cmf = table[selection, 1:4]
    dye = np.stack([np.interp(wavelengths, priors.PRINT_DYE_WAVELENGTHS_NM, priors.PRINT_DYE_CMY_SPECTRAL_DENSITY[:, c]) for c in range(3)], axis=1)
    illuminant = np.interp(wavelengths, priors.PRINT_DYE_WAVELENGTHS_NM, priors.KODAK_XENON_PROJECTOR_RELATIVE_SPD)
    trapezoid = np.ones(wavelengths.size)
    trapezoid[[0, -1]] = 0.5
    weighted_cmf = illuminant[:, None] * cmf * trapezoid[:, None]
    base = np.interp(wavelengths, priors.PRINT_DYE_WAVELENGTHS_NM, priors.PRINT_2383_DMIN_SPECTRAL_DENSITY)
    white = np.sum(weighted_cmf, axis=0)
    _PROJECTION_OPERATOR = {
        "wavelengths": wavelengths,
        "cmf": cmf,
        "trapezoid": trapezoid,
        "dye": dye,
        "weighted_cmf": weighted_cmf,
        "base": base,
        "white_y": white[1],
        "adaptation": bradford_to_d65(white / white[1]),
    }
    return _PROJECTION_OPERATOR


def projection_rgb_direct(print_density: np.ndarray, chunk: int = 32768) -> np.ndarray:
    """Linear Rec.709 light of projected 2383 density (clear film -> white)."""
    op = projection_operator()
    source = np.asarray(print_density, dtype=np.float64)
    flat = np.clip(source.reshape(-1, 3), 0.0, PRINT_DMAX)
    cmy = print_dye_amounts(flat)
    to_rec709 = np.asarray(priors.XYZ_D65_TO_REC709, dtype=np.float64)
    out = np.empty_like(flat, dtype=np.float32)
    for start in range(0, flat.shape[0], chunk):
        stop = min(start + chunk, flat.shape[0])
        spectral = np.clip(cmy[start:stop] @ op["dye"].T + op["base"][None, :], 0.0, 16.0)
        xyz = np.power(10.0, -spectral) @ op["weighted_cmf"] / op["white_y"]
        out[start:stop] = (xyz @ op["adaptation"].T) @ to_rec709.T
    return out.reshape(source.shape)


# ---------------------------------------------------------------------------
# Dense lattices (V87)
# ---------------------------------------------------------------------------


class DensityLattice:
    """Trilinear lattice over a shared power-spaced or uniform density axis."""

    def __init__(self, name: str, size: int, maximum: float, power: float, evaluate, progress=None) -> None:
        self.name = name
        self.size = int(size)
        self.maximum = float(maximum)
        self.power = float(power)
        self.axis = self.maximum * np.power(np.linspace(0.0, 1.0, self.size), self.power)
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        self.path = CACHE_ROOT / f"{name}_{self.size}_p{self.power:g}_{priors_fingerprint()}.npy"
        if self.path.exists():
            self.values = np.load(self.path, mmap_mode=None)
            if self.values.shape != (self.size, self.size, self.size, 3):
                self.values = None
        else:
            self.values = None
        if self.values is None:
            self.values = self._build(evaluate, progress)
            np.save(self.path, self.values)
        self.values = np.ascontiguousarray(self.values, dtype=np.float32)

    def _build(self, evaluate, progress) -> np.ndarray:
        size = self.size
        values = np.empty((size, size, size, 3), dtype=np.float32)
        b, c = np.meshgrid(self.axis, self.axis, indexing="ij")
        for i, a in enumerate(self.axis):
            target = np.stack([np.full_like(b, a), b, c], axis=-1).reshape(-1, 3)
            values[i] = evaluate(target).reshape(size, size, 3)
            if progress is not None:
                progress(i + 1, size)
        return values

    def _index(self, density: np.ndarray) -> np.ndarray:
        unit = np.clip(np.asarray(density, dtype=np.float32) / self.maximum, 0.0, 1.0)
        if self.power != 1.0:
            unit = np.power(unit, 1.0 / self.power)
        return np.clip(unit * (self.size - 1), 0.0, self.size - 1.00001).astype(np.float32)

    def sample(self, density: np.ndarray, chunk: int = 1_000_000) -> np.ndarray:
        source = np.asarray(density, dtype=np.float32)
        flat = np.ascontiguousarray(source.reshape(-1, 3))
        if fast.HAVE_NUMBA:
            index = fast.status_m_index(flat, np.float32(self.maximum), np.float32(1.0 / self.power), np.float32(self.size - 1))
            return fast.trilinear_sample(self.values, index).reshape(source.shape)
        out = np.empty_like(flat, dtype=np.float32)
        lut = self.values
        size = self.size
        for start in range(0, flat.shape[0], chunk):
            stop = min(start + chunk, flat.shape[0])
            scaled = self._index(flat[start:stop])
            lower = np.floor(scaled).astype(np.int32)
            fraction = scaled - lower
            upper = np.minimum(lower + 1, size - 1)
            a0, b0, c0 = lower[:, 0], lower[:, 1], lower[:, 2]
            a1, b1, c1 = upper[:, 0], upper[:, 1], upper[:, 2]
            fa, fb, fc = fraction[:, 0:1], fraction[:, 1:2], fraction[:, 2:3]
            x00 = lut[a0, b0, c0] * (1 - fa) + lut[a1, b0, c0] * fa
            x01 = lut[a0, b0, c1] * (1 - fa) + lut[a1, b0, c1] * fa
            x10 = lut[a0, b1, c0] * (1 - fa) + lut[a1, b1, c0] * fa
            x11 = lut[a0, b1, c1] * (1 - fa) + lut[a1, b1, c1] * fa
            out[start:stop] = (x00 * (1 - fc) + x01 * fc) * (1 - fb) + (x10 * (1 - fc) + x11 * fc) * fb
        return out.reshape(source.shape)


class SpectralModel:
    """The two V87 lattices plus the neutral-scale calibrations that use them."""

    PRINTER_SIZE = 129
    PRINTER_POWER = 2.0
    PROJECTION_SIZE = 129
    NEGATIVE_PREVIEW_SIZE = 33

    def __init__(self, progress=None) -> None:
        with _LOCK:
            self.printer = DensityLattice("printer_density", self.PRINTER_SIZE, MAX_RECORD_DENSITY, self.PRINTER_POWER, printer_density_direct, progress)
            self.projection = DensityLattice("projection_rgb", self.PROJECTION_SIZE, PRINT_DMAX, 1.0, projection_rgb_direct, progress)
            self.negative_preview = DensityLattice("negative_light_table", self.NEGATIVE_PREVIEW_SIZE, MAX_RECORD_DENSITY, 2.0, negative_light_table_rgb_direct, None)
        self.base_printing_density = self.printer.sample(np.zeros((1, 3), dtype=np.float32))[0]

    def printer_density(self, total_record_density: np.ndarray) -> np.ndarray:
        """Printer density of a formed negative; mean D-min integrated exactly once."""
        signed = np.asarray(total_record_density, dtype=np.float32) - priors.SENSITO_DMIN_RGB
        return (self.printer.sample(np.maximum(signed, 0.0)) + np.minimum(signed, 0.0)).astype(np.float32)

    def negative_light_table(self, total_record_density: np.ndarray) -> np.ndarray:
        signed = np.asarray(total_record_density, dtype=np.float32) - priors.SENSITO_DMIN_RGB
        return self.negative_preview.sample(np.maximum(signed, 0.0))


_MODEL: SpectralModel | None = None


def spectral_model(progress=None) -> SpectralModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = SpectralModel(progress)
    return _MODEL


# ---------------------------------------------------------------------------
# Optional Numba acceleration of the joint inverse (same equations)
# ---------------------------------------------------------------------------

try:  # pragma: no cover - exercised when numba is installed
    import numba

    @numba.njit(parallel=True, cache=True)
    def _solve_cmy_numba(target, weights, dmin, spectra, base_density, origin_inverse, iterations):
        n = target.shape[0]
        nl = weights.shape[0]
        out = np.empty((n, 3), dtype=np.float64)
        for p in numba.prange(n):
            t0 = max(target[p, 0], 0.0)
            t1 = max(target[p, 1], 0.0)
            t2 = max(target[p, 2], 0.0)
            c = np.empty(3)
            for j in range(3):
                c[j] = max(t0 * origin_inverse[j, 0] + t1 * origin_inverse[j, 1] + t2 * origin_inverse[j, 2], 0.0)
            jac = np.empty((3, 3))
            dens = np.empty(3)
            integ = np.empty(3)
            for _ in range(iterations):
                for j in range(3):
                    integ[j] = 0.0
                    jac[j, 0] = 0.0
                    jac[j, 1] = 0.0
                    jac[j, 2] = 0.0
                for l in range(nl):
                    s0 = spectra[l, 0]
                    s1 = spectra[l, 1]
                    s2 = spectra[l, 2]
                    tr = np.exp(-2.302585092994046 * (dmin[l] + c[0] * s0 + c[1] * s1 + c[2] * s2))
                    for j in range(3):
                        tw = tr * weights[l, j]
                        integ[j] += tw
                        jac[j, 0] += tw * s0
                        jac[j, 1] += tw * s1
                        jac[j, 2] += tw * s2
                for j in range(3):
                    if integ[j] < 1e-30:
                        integ[j] = 1e-30
                    dens[j] = -np.log10(integ[j]) - base_density[j]
                    jac[j, 0] /= integ[j]
                    jac[j, 1] /= integ[j]
                    jac[j, 2] /= integ[j]
                r0 = dens[0] - t0
                r1 = dens[1] - t1
                r2 = dens[2] - t2
                # normal = J^T J + 1e-8 I ; gradient = J^T r
                nm = np.empty((3, 3))
                g = np.empty(3)
                for i in range(3):
                    for k in range(3):
                        s = 0.0
                        for j in range(3):
                            s += jac[j, i] * jac[j, k]
                        nm[i, k] = s
                    nm[i, i] += 1e-8
                    g[i] = jac[0, i] * r0 + jac[1, i] * r1 + jac[2, i] * r2
                step = -np.linalg.solve(nm, g)
                m = max(abs(step[0]), max(abs(step[1]), abs(step[2])))
                damping = max(1.0, m / 0.5)
                for j in range(3):
                    v = c[j] + step[j] / damping
                    if v < 0.0:
                        v = 0.0
                    elif v > 12.0:
                        v = 12.0
                    c[j] = v
            out[p, 0] = c[0]
            out[p, 1] = c[1]
            out[p, 2] = c[2]
        return out

    def solve_cmy_from_status_m_fast(status_m_net_density: np.ndarray, iterations: int = 24) -> np.ndarray:
        weights, dmin, spectra, base_density = _STATUS_M
        source = np.asarray(status_m_net_density, dtype=np.float64)
        flat = np.ascontiguousarray(source.reshape(-1, 3))
        with np.errstate(all="ignore"):
            transmission = np.power(10.0, -dmin)[None, :]
            integrated = np.maximum(transmission @ weights, 1e-30)
            origin_jacobian = np.einsum("nl,lj,lk->njk", transmission, weights, spectra)[0] / integrated[0][:, None]
        origin_inverse = np.ascontiguousarray(np.linalg.inv(origin_jacobian).T)
        keep = np.any(weights != 0.0, axis=1)
        result = _solve_cmy_numba(
            flat, np.ascontiguousarray(weights[keep]), np.ascontiguousarray(dmin[keep]),
            np.ascontiguousarray(spectra[keep]), base_density, origin_inverse, int(iterations),
        )
        return result.reshape(source.shape).astype(np.float32)

    HAVE_NUMBA = True
except Exception:  # pragma: no cover
    HAVE_NUMBA = False
    solve_cmy_from_status_m_fast = solve_cmy_from_status_m
