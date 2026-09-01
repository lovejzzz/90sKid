"""Frame pipeline: parameters, presets and the per-frame render entry point."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
import time

import numpy as np

from .colour import TRANSFER_DECODERS, apply_matrix, bt1886_encode, gamut_to_rec709_matrix, srgb_encode
from .negative import form_negative
from .observers import Observers, observers as default_observers

FILM_GAUGES = {
    "super35": {"label": "Super 35 (24.89 mm)", "width_mm": 24.89},
    "academy35": {"label": "35 mm Academy (21.95 mm)", "width_mm": 21.95},
    "super16": {"label": "Super 16 (12.52 mm)", "width_mm": 12.52},
    "regular16": {"label": "16 mm (10.26 mm)", "width_mm": 10.26},
    "vistavision": {"label": "VistaVision 8-perf (37.72 mm)", "width_mm": 37.72},
}


@dataclass
class FilmParams:
    """Every user-adjustable control.  Defaults are the Kodak 5279 baseline."""

    # input interpretation
    input_transfer: str = "bt709"
    input_gamut: str = "rec709"
    exposure_stops: float = 0.0
    sensor_noise_separation: bool = True
    chroma_residual: float = 0.0
    # stock and gate
    gauge: str = "super35"
    halation: float = 1.0
    grain_scale: float = 1.0
    grain_amount: float = 1.0
    size_classes: int = 5
    grain_policy: str = "common"  # V49 common density | "independent" records
    oversample: int = 1
    seed: int = 0
    grain_sampler: str = "fast"  # counter-based Numba sampler | "archive" NumPy striped binomial
    # observers
    colour_authority: str = "physical"  # or "scan_referenced"
    projector_flare: float = 0.0
    scan_width: int = 2048
    bluray_grain: str = "direct"  # V49 direct | "managed" historical V46 finish
    # delivery
    output_transfer: str = "bt1886"  # or "srgb"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FilmParams":
        allowed = {f.name: f.type for f in fields(cls)}
        kwargs = {}
        for key, value in (data or {}).items():
            if key not in allowed:
                continue
            default = getattr(cls(), key)
            if isinstance(default, bool):
                kwargs[key] = bool(value) if not isinstance(value, str) else value.lower() in ("1", "true", "yes", "on")
            elif isinstance(default, int):
                kwargs[key] = int(round(float(value)))
            elif isinstance(default, float):
                kwargs[key] = float(value)
            else:
                kwargs[key] = str(value)
        params = cls(**kwargs)
        params.validate()
        return params

    def validate(self) -> None:
        if self.input_transfer not in TRANSFER_DECODERS:
            raise ValueError(f"unknown input transfer {self.input_transfer}")
        if self.gauge not in FILM_GAUGES:
            raise ValueError(f"unknown film gauge {self.gauge}")
        self.size_classes = 5 if self.size_classes >= 5 else (3 if self.size_classes >= 3 else 1)
        self.oversample = 2 if self.oversample >= 2 else 1
        self.exposure_stops = float(np.clip(self.exposure_stops, -6.0, 6.0))
        self.grain_scale = float(np.clip(self.grain_scale, 0.25, 4.0))
        self.grain_amount = float(np.clip(self.grain_amount, 0.0, 2.0))
        self.halation = float(np.clip(self.halation, 0.0, 4.0))
        self.chroma_residual = float(np.clip(self.chroma_residual, 0.0, 1.0))
        self.projector_flare = float(np.clip(self.projector_flare, 0.0, 0.05))
        self.scan_width = int(np.clip(self.scan_width, 256, 8192))
        if self.grain_sampler not in ("fast", "archive"):
            raise ValueError("grain_sampler must be 'fast' or 'archive'")
        if self.grain_policy not in ("common", "independent"):
            raise ValueError("grain_policy must be 'common' or 'independent'")
        if self.colour_authority not in ("physical", "scan_referenced"):
            raise ValueError("colour_authority must be 'physical' or 'scan_referenced'")
        if self.bluray_grain not in ("direct", "managed"):
            raise ValueError("bluray_grain must be 'direct' or 'managed'")
        if self.output_transfer not in ("bt1886", "srgb"):
            raise ValueError("output_transfer must be 'bt1886' or 'srgb'")


PRESETS = {
    "kodak_5279_baseline": {"label": "Kodak 5279 baseline (V49 common density)", "params": {}},
    "gh7_prores_raw": {"label": "GH7 ProRes RAW research baseline (+0.45 stop, chart residual)", "params": {"exposure_stops": 0.45, "chroma_residual": 0.125, "input_transfer": "linear", "input_gamut": "bt2020"}},
    "independent_records": {"label": "Independent record grain (V72 full realization)", "params": {"grain_policy": "independent"}},
    "super16": {"label": "Super 16 gate (coarser grain, same stock)", "params": {"gauge": "super16"}},
    "clean_print": {"label": "Deterministic print (no grain)", "params": {"grain_amount": 0.0}},
}


def decode_to_scene_linear(encoded_rgb: np.ndarray, params: FilmParams) -> np.ndarray:
    """Encoded [0,1] RGB in the source transfer/gamut -> linear Rec.709 basis."""
    linear = TRANSFER_DECODERS[params.input_transfer](np.asarray(encoded_rgb, dtype=np.float32))
    if params.input_gamut != "rec709":
        linear = apply_matrix(linear, gamut_to_rec709_matrix(params.input_gamut))
    return np.maximum(linear, 0.0).astype(np.float32)


def encode_display(linear_rec709: np.ndarray, transfer: str) -> np.ndarray:
    return srgb_encode(linear_rec709) if transfer == "srgb" else bt1886_encode(linear_rec709)


class FrameResult:
    __slots__ = ("projection", "scan", "negative", "cineon_code", "seconds", "mean_projection", "mean_scan")

    def __init__(self) -> None:
        self.projection = None
        self.scan = None
        self.negative = None
        self.cineon_code = None
        self.mean_projection = None
        self.mean_scan = None
        self.seconds = {}


def render_frame(
    scene_rec709_linear: np.ndarray,
    frame_index: int,
    params: FilmParams,
    *,
    want=("projection", "scan"),
    obs: Observers | None = None,
    reference_width: int | None = None,
) -> FrameResult:
    """Form one negative and observe it through the requested branches.

    ``reference_width`` lets a 1:1 crop preview keep the grain geometry of the
    full raster it was cut from.
    """
    obs = obs or default_observers()
    result = FrameResult()
    t0 = time.perf_counter()
    negative = form_negative(
        scene_rec709_linear,
        frame_index,
        exposure_stops=params.exposure_stops,
        gate_width_mm=FILM_GAUGES[params.gauge]["width_mm"],
        halation=params.halation,
        sensor_noise_separation=params.sensor_noise_separation,
        chroma_residual=params.chroma_residual,
        grain_scale=params.grain_scale,
        grain_amount=params.grain_amount,
        size_classes=params.size_classes,
        grain_policy=params.grain_policy,
        oversample=params.oversample,
        seed=params.seed,
        reference_width=reference_width,
        sampler=params.grain_sampler,
    )
    printer = obs.model.printer_density(negative.formed)
    t1 = time.perf_counter()
    result.seconds["negative"] = t1 - t0

    need_scan = "scan" in want or params.colour_authority == "scan_referenced" or "cineon" in want
    scan_view = None
    if need_scan:
        if params.bluray_grain == "managed" and params.grain_amount > 0.0:
            mean_view = obs.scan(negative.mean, params.scan_width)
            formed_view, code = obs.scan(negative.formed, params.scan_width, return_code=True, printer_density=printer)
            scan_view = obs.managed_bluray_grain(mean_view, formed_view)
            result.mean_scan = mean_view
        else:
            scan_view, code = obs.scan(negative.formed, params.scan_width, return_code=True, printer_density=printer)
        result.scan = scan_view
        result.cineon_code = code
    t2 = time.perf_counter()
    result.seconds["scan"] = t2 - t1

    if "projection" in want:
        result.projection = obs.project(
            negative.formed,
            negative.native_scale,
            params.grain_scale,
            colour_authority=params.colour_authority,
            scan_reference=scan_view,
            flare=params.projector_flare,
            printer_density=printer,
        )
    t3 = time.perf_counter()
    result.seconds["projection"] = t3 - t2

    if "negative" in want:
        result.negative = obs.negative_light_table(negative.formed)
    result.seconds["total"] = time.perf_counter() - t0
    return result
