"""The two material observers of one formed 5279 negative.

Projection ("film print"):
    formed negative -> printer density -> 2383 Status-A density (LAD lights)
    -> print MTF -> Callier -> xenon / CIE projection -> gray-scale neutral
    calibration -> print viewing curve -> monitor display curve.

Scan ("Blu-ray"):
    formed negative -> printing density above D-min (Cineon data contract)
    -> Spirit 2K aperture -> 10-bit Cineon code -> open display policy
    -> Blu-ray finish -> gray-scale balance.

Every calibration table is derived from a neutral exposure wedge through the
same equations, so a neutral scene stays neutral by construction.  No colour
chart, hand-tuned matrix or creative grade enters either branch.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

from . import priors
from .colour import compress_oklab_chroma_to_rec709, compress_unit_gamut, linear_rec709_to_oklab, luma, oklab_to_linear_rec709, smoothstep
from .negative import activation_probabilities, develop_record_density, film_records, hd_density, log_exposure_from_records
from .spectral import PRINT_DMAX, SpectralModel, apply_callier, print_density_from_printer_density, spectral_model

PRINT_MTF_SIGMAS_RGB = (0.34, 0.27, 0.52)
PRINT_VIEW_PEAK = 0.965
CINEON_MID_DENSITY = 0.700
CINEON_TOE_WIDTH = 0.008


def _neutral_wedge(stops_low: float = -12.0, stops_high: float = 9.0, samples: int = 337) -> np.ndarray:
    levels = 0.18 * np.power(2.0, np.linspace(stops_low, stops_high, samples, dtype=np.float32))
    return np.repeat(levels[:, None], 3, axis=1).astype(np.float32)


class Observers:
    """Calibrated projection and scan observers bound to one spectral model."""

    def __init__(self, model: SpectralModel | None = None) -> None:
        self.model = model or spectral_model()
        self.neutral_negative_printer = self._developed_printer_density(np.array([[0.18, 0.18, 0.18]], dtype=np.float32))[0]
        self.neutral_mid_scanner = self._plain_scanner_density(np.array([[0.18, 0.18, 0.18]], dtype=np.float32))[0]
        self.neutral_high_scanner = self._plain_scanner_density(np.array([[10.0, 10.0, 10.0]], dtype=np.float32))[0]
        self.view_neutral_table = self._build_view_neutral_table()
        self.lad_transmission = self._lad_transmission()
        self.spirit_neutral_table = self._build_spirit_neutral_table()
        self.monitor_curve = self._build_monitor_neutral_curve()

    # ---- negative helpers ---------------------------------------------------

    def _developed_printer_density(self, film_rgb: np.ndarray) -> np.ndarray:
        """Deterministic neutral path incl. DIR, as the printer sees it."""
        records = film_records(film_rgb)
        log_exposure = log_exposure_from_records(records)[None, ...]
        total = develop_record_density(log_exposure, activation_probabilities(log_exposure), 1.0)[0]
        return self.model.printer_density(total)

    def _plain_scanner_density(self, film_rgb: np.ndarray) -> np.ndarray:
        """Scanner reference points use the published H-D curve directly."""
        total = hd_density(log_exposure_from_records(film_records(film_rgb)))
        return self.model.printer_density(total) - self.model.base_printing_density

    # ---- projection ----------------------------------------------------------

    def print_density(self, negative_printer_density: np.ndarray) -> np.ndarray:
        return print_density_from_printer_density(negative_printer_density, self.neutral_negative_printer)

    def _projected_rgb(self, print_density: np.ndarray) -> np.ndarray:
        return np.maximum(self.model.projection.sample(apply_callier(print_density)), 0.0)

    def _build_view_neutral_table(self):
        wedge = _neutral_wedge()
        printer = self._developed_printer_density(wedge)
        rgb = np.maximum(self._projected_rgb(self.print_density(printer)), 1e-8)
        y = luma(rgb)
        factors = np.clip(y[:, None] / rgb, 0.35, 2.50)
        order = np.argsort(y)
        y, factors = y[order], factors[order]
        y, unique = np.unique(y, return_index=True)
        return y.astype(np.float32), factors[unique].astype(np.float32)

    def _neutralize_projected(self, projected: np.ndarray) -> np.ndarray:
        axis, table = self.view_neutral_table
        y = luma(np.maximum(projected, 0.0))
        out = np.empty_like(projected, dtype=np.float32)
        for c in range(3):
            out[..., c] = projected[..., c] * np.interp(y, axis, table[:, c])
        return np.maximum(out, 0.0).astype(np.float32)

    def _lad_transmission(self) -> float:
        lad = np.asarray(priors.PRINT_2383_LAD_PRINCIPAL_DENSITY_RGB, dtype=np.float32)[None, :]
        projected = self._neutralize_projected(self._projected_rgb(lad))
        return float(luma(projected)[0])

    def _view_curve(self, projected: np.ndarray) -> np.ndarray:
        """Rational print-viewing adaptation: LAD -> 18 %, clear film -> peak."""
        ratio = 0.18 / PRINT_VIEW_PEAK
        a = self.lad_transmission * (1.0 - ratio) / max(ratio - self.lad_transmission, 1e-6)
        viewed = PRINT_VIEW_PEAK * projected * (1.0 + a) / (projected + a)
        return np.clip(compress_unit_gamut(viewed), 0.0, 1.0).astype(np.float32)

    def physical_projection(self, print_density: np.ndarray) -> np.ndarray:
        """Projected 2383 light in linear Rec.709 before the monitor display curve."""
        return self._view_curve(self._neutralize_projected(self._projected_rgb(print_density)))

    def _build_monitor_neutral_curve(self):
        wedge = _neutral_wedge()
        records = film_records(wedge)
        log_exposure = log_exposure_from_records(records)[None, ...]
        total = develop_record_density(log_exposure, activation_probabilities(log_exposure), 1.0)[0]
        printer = self.model.printer_density(total)
        physical = self.physical_projection(self.print_density(printer))
        scan = self.finish_bluray(self.open_display(self.cineon_code(printer - self.model.base_printing_density)))
        physical_axis = np.mean(physical, axis=-1)
        target = np.interp(luma(np.maximum(scan, 0.0)), priors.PRINT_MONITOR_SCAN_LUMA_ANCHORS, priors.PRINT_MONITOR_TARGET_LUMA_ANCHORS)
        order = np.argsort(physical_axis)
        physical_axis, target = physical_axis[order], target[order]
        physical_axis, unique = np.unique(physical_axis, return_index=True)
        return physical_axis.astype(np.float32), target[unique].astype(np.float32)

    def monitor_display(self, physical: np.ndarray) -> np.ndarray:
        x, y = self.monitor_curve
        out = np.empty_like(physical, dtype=np.float32)
        for c in range(3):
            out[..., c] = np.interp(physical[..., c], x, y).astype(np.float32)
        return out

    def project(
        self,
        formed_total_density: np.ndarray,
        native_scale: float,
        grain_scale: float,
        *,
        colour_authority: str = "physical",
        scan_reference: np.ndarray | None = None,
        flare: float = 0.0,
        printer_density: np.ndarray | None = None,
    ) -> np.ndarray:
        """Complete projection observer -> linear Rec.709 display light."""
        printer = self.model.printer_density(formed_total_density) if printer_density is None else printer_density
        print_density = self.print_density(printer)
        scale = native_scale * grain_scale
        for c, sigma in enumerate(PRINT_MTF_SIGMAS_RGB):
            print_density[..., c] = cv2.GaussianBlur(print_density[..., c], (0, 0), max(sigma * scale, 0.05), borderType=cv2.BORDER_REFLECT)
        physical = self.physical_projection(print_density)
        if flare > 0.0:
            physical = ((physical + flare) / (1.0 + flare)).astype(np.float32)
        view = self.monitor_display(physical)
        if colour_authority == "scan_referenced" and scan_reference is not None:
            physical_lab = linear_rec709_to_oklab(view)
            scan_lab = linear_rec709_to_oklab(np.clip(scan_reference, 0.0, 1.0))
            physical_max = np.max(view, axis=-1)
            relative_chroma = (physical_max - np.min(view, axis=-1)) / np.maximum(physical_max, 1e-6)
            weight = smoothstep(0.02, 0.12, relative_chroma)[..., None]
            matched = physical_lab.copy()
            matched[..., 1:3] = physical_lab[..., 1:3] * (1.0 - weight) + scan_lab[..., 1:3] * weight
            view = oklab_to_linear_rec709(matched)
        return compress_oklab_chroma_to_rec709(view)

    # ---- scan ------------------------------------------------------------------

    def scanner_density(self, formed_total_density: np.ndarray) -> np.ndarray:
        return (self.model.printer_density(formed_total_density) - self.model.base_printing_density).astype(np.float32)

    @staticmethod
    def spirit_aperture(scanner_density: np.ndarray, scan_width: int = 2048) -> np.ndarray:
        """Integrate transmission through the period 2K scanner aperture."""
        h, w = scanner_density.shape[:2]
        if h < 4 or w < 4:
            return scanner_density
        scan_w = min(scan_width, w)
        scan_h = max(2, round(h * scan_w / w))
        scan_h -= scan_h % 2
        transmission = np.power(10.0, -np.clip(scanner_density, -0.25, 4.0)).astype(np.float32)
        sampled = cv2.resize(transmission, (scan_w, scan_h), interpolation=cv2.INTER_AREA)
        density = -np.log10(np.maximum(sampled, 1e-6))
        softened = cv2.GaussianBlur(density, (0, 0), 0.48, borderType=cv2.BORDER_REFLECT)
        aperture = density + 0.11 * (density - softened)
        if scan_w == w and scan_h == h:
            return aperture.astype(np.float32)
        return cv2.resize(aperture, (w, h), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)

    def cineon_code(self, scanner_density: np.ndarray) -> np.ndarray:
        """Exact unsigned 10-bit printing-density code (Kodak 0.002 D/code, black 95)."""
        gain = CINEON_MID_DENSITY / np.maximum(self.neutral_mid_scanner, 1e-6)
        code = 95.0 + scanner_density * gain / 0.002
        return np.clip(np.rint(code), 0.0, 1023.0).astype(np.uint16)

    def open_display(self, cineon_code: np.ndarray) -> np.ndarray:
        """The named open-monitor policy for Cineon exchange data (V66)."""
        code = np.asarray(cineon_code).astype(np.float32)
        gain = CINEON_MID_DENSITY / np.maximum(self.neutral_mid_scanner, 1e-6)
        decoded = (code - 95.0) * 0.002
        decoded = 0.5 * (decoded + np.sqrt(decoded * decoded + CINEON_TOE_WIDTH**2))
        high = self.neutral_high_scanner * gain
        high_toe = 0.5 * (high + np.sqrt(high * high + CINEON_TOE_WIDTH**2))
        mid_toe = 0.5 * (CINEON_MID_DENSITY + math.sqrt(CINEON_MID_DENSITY**2 + CINEON_TOE_WIDTH**2))
        unit = decoded / np.maximum(high_toe, 1e-6)
        neutral_mid_unit = mid_toe / np.maximum(high_toe, 1e-6)
        peak = np.array([0.90, 0.90, 0.90], dtype=np.float32)
        power = np.log(0.18 / peak) / np.log(np.maximum(neutral_mid_unit, 1e-5))
        mapped = peak * np.power(np.clip(unit, 0.0, 1.25), power)
        return compress_unit_gamut(mapped).astype(np.float32)

    @staticmethod
    def finish_bluray(scan_linear: np.ndarray) -> np.ndarray:
        """Restrained SDR finishing trim: 1.20 lower-scale gamma anchored at 18 %."""
        rgb = np.maximum(np.asarray(scan_linear, dtype=np.float32), 0.0)
        y = luma(rgb)
        lower = np.where(y > 0.0, 0.18 * np.power(np.maximum(y, 0.0) / 0.18, 1.20), 0.0)
        blend = smoothstep(0.12, 0.30, y)
        target = lower * (1.0 - blend) + y * blend
        return compress_oklab_chroma_to_rec709(rgb * (target / np.maximum(y, 1e-8))[..., None])

    def _build_spirit_neutral_table(self):
        samples = max(int(priors.SPIRIT_NEUTRAL_SCALE_CALIBRATION_SAMPLES), 257)
        positive = np.geomspace(1e-5, float(priors.SPIRIT_NEUTRAL_SCALE_CALIBRATION_MAX_SCENE_LINEAR), samples - 1, dtype=np.float32)
        levels = np.concatenate([np.zeros(1, dtype=np.float32), positive])
        wedge = np.repeat(levels[:, None], 3, axis=1)
        records = film_records(wedge)
        log_exposure = log_exposure_from_records(records)[None, ...]
        total = develop_record_density(log_exposure, activation_probabilities(log_exposure), 1.0)[0]
        finished = self.finish_bluray(self.open_display(self.cineon_code(self.scanner_density(total))))
        target = luma(np.maximum(finished, 0.0))
        factors = np.clip(target[:, None] / np.maximum(finished, 1e-8), 0.35, 2.50)
        order = np.argsort(target, kind="stable")
        target, factors = target[order], factors[order]
        unique_luma, first, counts = np.unique(target, return_index=True, return_counts=True)
        unique_factors = np.add.reduceat(factors, first, axis=0) / counts[:, None]
        if unique_luma[0] > 0.0:
            unique_luma = np.concatenate([np.zeros(1, dtype=np.float32), unique_luma])
            unique_factors = np.concatenate([np.ones((1, 3), dtype=np.float32), unique_factors], axis=0)
        if unique_luma[-1] < 1.0:
            unique_luma = np.concatenate([unique_luma, np.ones(1, dtype=np.float32)])
            unique_factors = np.concatenate([unique_factors, np.ones((1, 3), dtype=np.float32)], axis=0)
        return unique_luma.astype(np.float32), unique_factors.astype(np.float32)

    def neutralize_scan(self, display_linear: np.ndarray) -> np.ndarray:
        source = np.clip(np.asarray(display_linear, dtype=np.float32), 0.0, 1.0)
        axis, table = self.spirit_neutral_table
        y = luma(source)
        factors = np.empty_like(source)
        for c in range(3):
            factors[..., c] = np.interp(y, axis, table[:, c]).astype(np.float32)
        corrected = source * factors
        corrected *= (y / np.maximum(luma(corrected), 1e-8))[..., None]
        corrected = np.where((y > 0.0)[..., None], corrected, 0.0)
        return compress_unit_gamut(corrected).astype(np.float32)

    def scan(self, formed_total_density: np.ndarray, scan_width: int = 2048, *, return_code: bool = False, printer_density: np.ndarray | None = None):
        """Complete scan / Blu-ray observer -> linear Rec.709 display light."""
        scanner = (
            self.scanner_density(formed_total_density)
            if printer_density is None
            else (printer_density - self.model.base_printing_density).astype(np.float32)
        )
        density = self.spirit_aperture(scanner, scan_width)
        code = self.cineon_code(density)
        view = self.neutralize_scan(compress_oklab_chroma_to_rec709(self.finish_bluray(self.open_display(code))))
        if return_code:
            return view, code
        return view

    def managed_bluray_grain(self, mean_view: np.ndarray, formed_view: np.ndarray) -> np.ndarray:
        """Historical V46 Blu-ray finish: keep luma grain, integrate opponent grain."""
        delta = formed_view - mean_view
        luma_delta = luma(delta)
        opponent = delta - luma_delta[..., None]
        sigma = max(priors.BLURAY_CHROMA_GRAIN_SIGMA_AT_2K * mean_view.shape[1] / 2048.0, 0.05)
        low = cv2.GaussianBlur(opponent, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
        opponent = (low + priors.BLURAY_CHROMA_GRAIN_HIGH_FREQUENCY_RETENTION * (opponent - low)) * priors.BLURAY_CHROMA_GRAIN_OPPONENT_STRENGTH
        visibility = smoothstep(0.0012, 0.018, luma(np.maximum(mean_view, 0.0)))
        managed = (luma_delta[..., None] + opponent) * visibility[..., None]
        return compress_oklab_chroma_to_rec709(mean_view + managed)

    # ---- negative preview -----------------------------------------------------

    def negative_light_table(self, formed_total_density: np.ndarray) -> np.ndarray:
        """The orange-masked negative on a 3200 K light table (preview only)."""
        rgb = self.model.negative_light_table(formed_total_density)
        return np.clip(rgb / max(float(np.max(self.model.negative_light_table(priors.SENSITO_DMIN_RGB[None, :]))), 1e-6), 0.0, 1.0).astype(np.float32)


_OBSERVERS: Observers | None = None


def observers() -> Observers:
    global _OBSERVERS
    if _OBSERVERS is None:
        _OBSERVERS = Observers()
    return _OBSERVERS
