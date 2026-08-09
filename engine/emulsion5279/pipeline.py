"""Second-generation, explicit-stage V41 frame engine."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time

import cv2
import numpy as np

from .assets import PRINT_2383_OUTPUT_LATTICE, verify_v41_runtime_assets
from .contracts import (
    DeliveryEncoding,
    EncodedObserverPair,
    EngineConfig,
    EngineMode,
    ObserverPair,
    RenderedFrame,
)
from . import legacy


_CONFIGURE_LOCK = threading.Lock()
_RENDER_LOCK = threading.Lock()
_ACTIVE_CONFIG: EngineConfig | None = None


@dataclass(slots=True)
class FormedNegative:
    """Mean and realized density from one shared 5279 exposure."""

    mean_record_density: np.ndarray
    formed_record_density: np.ndarray


class Emulsion5279Engine:
    """Own a configured V41 graph without exposing historical profile mutation."""

    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()
        self._configured = False

    @property
    def provenance(self) -> dict[str, object]:
        return {
            "engine_api": "emulsion5279-v2",
            "profile": self.config.profile,
            "input_colour_contract": self.config.input_colour.value,
            "delivery_contract": [
                DeliveryEncoding.REFERENCE_BT1886.value,
                DeliveryEncoding.QUICKTIME_SRGB.value,
            ],
            "print_lattice_sha256": PRINT_2383_OUTPUT_LATTICE.sha256,
            **legacy.source_fingerprints(),
        }

    def configure(self) -> None:
        """Select V41 once and install only output-identical acceleration."""
        global _ACTIVE_CONFIG
        if self._configured:
            return
        with _CONFIGURE_LOCK:
            if self._configured:
                return
            if _ACTIVE_CONFIG is not None and _ACTIVE_CONFIG != self.config:
                raise RuntimeError(
                    "the archival V41 backend owns process-global caches; use one "
                    "EngineConfig per process until the remaining kernels are lifted"
                )
            verify_v41_runtime_assets()
            e = legacy.model
            legacy.profile.apply(e)
            cv2.setNumThreads(self.config.opencv_threads)
            e.BINOMIAL_PARALLEL_WORKERS = self.config.binomial_workers
            e._PRINT_2383_MONITOR_OUTPUT_LUT = np.load(
                PRINT_2383_OUTPUT_LATTICE.path, allow_pickle=False
            )
            if self.config.mode is EngineMode.ARCHIVE_EXACT_CPU:
                import v27_accel

                v27_accel.apply(
                    e,
                    numba_threads=self.config.numba_threads,
                    array_workers=self.config.array_workers,
                    exact_only=True,
                )
                v27_accel.warm(e)
            _ACTIVE_CONFIG = self.config
            self._configured = True

    @staticmethod
    def _validate_raw_frame(raw: np.ndarray) -> np.ndarray:
        frame = np.asarray(raw, dtype=np.float32)
        if frame.ndim != 3 or frame.shape[-1] != 3:
            raise ValueError("decoded RAW frame must have shape height x width x RGB")
        if not np.all(np.isfinite(frame)):
            raise ValueError("decoded RAW frame contains non-finite samples")
        # Extended-linear highlights are deliberately allowed above one.
        return frame

    def form_negative(self, raw: np.ndarray, absolute_frame: int) -> FormedNegative:
        self.configure()
        e = legacy.model
        frame = self._validate_raw_frame(raw)
        film_rgb = e.scene_to_5279_film_rgb(
            frame,
            exposure_stops=self.config.exposure_stops,
            raw_colour=legacy.profile.PROFILE["raw_colour"],
            include_optical_scatter=True,
            sensor_noise_treatment="photochemical",
        )
        records = e.film_records_from_rgb(film_rgb)
        mean = e.develop_5279_record_density(records)
        formed = e.form_5279_multilayer_record_density(
            records,
            int(absolute_frame),
            self.config.grain_scale,
            self.config.oversample,
            precomputed_mean_density=(mean if self.config.oversample == 1 else None),
        )
        return FormedNegative(mean, formed)

    def observe(self, negative: FormedNegative, absolute_frame: int) -> ObserverPair:
        self.configure()
        projection, scan = legacy.model.reconstruct_density_pair_to_dual_display_v39(
            negative.mean_record_density,
            negative.formed_record_density,
            int(absolute_frame),
            self.config.grain_scale,
            "linear_rec709",
        )
        from apply_v31_normal_process_adapter import adapt_frame_linear

        projection = adapt_frame_linear(
            projection,
            scan,
            legacy.profile.PROFILE.get(
                "final_adapter_opponent_high_frequency_retention", 1.0
            ),
        )
        return ObserverPair(projection, scan)

    @staticmethod
    def encode(observers: ObserverPair) -> tuple[EncodedObserverPair, EncodedObserverPair]:
        e = legacy.model
        master = EncodedObserverPair(
            projection=e.bt1886_reference_encode(observers.projection_linear_rec709),
            scan=e.bt1886_reference_encode(observers.scan_linear_rec709),
            encoding=DeliveryEncoding.REFERENCE_BT1886,
        )
        quicktime = EncodedObserverPair(
            projection=e.srgb_encode(observers.projection_linear_rec709).astype(np.float32),
            scan=e.srgb_encode(observers.scan_linear_rec709).astype(np.float32),
            encoding=DeliveryEncoding.QUICKTIME_SRGB,
        )
        return master, quicktime

    def render_frame(self, raw: np.ndarray, absolute_frame: int) -> RenderedFrame:
        """Form one negative once, then derive both observers and deliveries."""
        # The recovered backend still owns mutable module caches. Serializing
        # frame entry prevents an accidental multi-instance race from changing
        # colour or stochastic state. A future resident Metal backend will own
        # per-instance resources and can remove this compatibility lock.
        with _RENDER_LOCK:
            started = time.perf_counter()
            negative = self.form_negative(raw, absolute_frame)
            formed_at = time.perf_counter()
            observers = self.observe(negative, absolute_frame)
            observed_at = time.perf_counter()
            master, quicktime = self.encode(observers)
            encoded_at = time.perf_counter()
        return RenderedFrame(
            absolute_frame=int(absolute_frame),
            observers=observers,
            reference_master=master,
            quicktime_companion=quicktime,
            stage_seconds={
                "negative_formation": formed_at - started,
                "dual_observer": observed_at - formed_at,
                "delivery_encoding": encoded_at - observed_at,
                "total": encoded_at - started,
            },
        )
