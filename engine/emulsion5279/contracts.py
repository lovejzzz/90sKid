"""Typed stage and colour contracts for the 5279 reconstruction graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping

import numpy as np


class InputColourContract(str, Enum):
    """The colour interpretation of a decoded source frame."""

    AVFOUNDATION_EXTENDED_LINEAR_BT2020 = "avfoundation_extended_linear_bt2020_d65"


class DeliveryEncoding(str, Enum):
    """Two explicit encodings of the same display-linear observer light."""

    REFERENCE_BT1886 = "rec709_primaries_bt1886_gamma24"
    QUICKTIME_SRGB = "rec709_primaries_srgb_transfer"


class EngineMode(str, Enum):
    """Execution choices; none changes the selected film model."""

    REFERENCE = "reference_numpy"
    ARCHIVE_EXACT_CPU = "archive_exact_cpu"
    PRODUCTION_METAL = "production_philox_metal"


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """Immutable controls that may legitimately vary between renders.

    Film parameters do not live here.  V41 is an evidence baseline, not a
    creative preset: sensitometry, DIR, MTF, grain statistics, black and the
    two observers are owned by the versioned profile.
    """

    profile: str = "v42"
    input_colour: InputColourContract = (
        InputColourContract.AVFOUNDATION_EXTENDED_LINEAR_BT2020
    )
    exposure_stops: float = 0.45
    grain_scale: float = 1.0
    oversample: int = 1
    mode: EngineMode = EngineMode.PRODUCTION_METAL
    opencv_threads: int = 8
    binomial_workers: int = 8
    numba_threads: int = 8
    array_workers: int = 8
    observer_branch_workers: int = 1
    grain_domain_salt: int = 0
    research_baseline: bool = True

    def __post_init__(self) -> None:
        if self.profile not in {
            "v42", "v43h", "v44", "v45", "v46", "v48", "v49", "v50", "v51", "v52", "v53", "v54", "v55", "v56", "v57", "v58", "v59", "v60", "v61", "v62", "v63", "v64", "v66", "v72"
        }:
            raise ValueError(
                "the emulsion engine supports V42, V43H, V44, V45, V46, V48, V49, V50, V51, V52, V53, V54, V55, V56, V57, V58, V59, V60, V61, V62, V63, V64, V66 and V72 profiles"
            )
        if self.oversample < 1:
            raise ValueError("oversample must be positive")
        if self.grain_scale < 0.0:
            raise ValueError("grain_scale cannot be negative")
        if not 0 <= int(self.grain_domain_salt) <= 0xFFFFFFFF:
            raise ValueError("grain_domain_salt must fit uint32")
        if self.research_baseline:
            baseline = {
                "exposure_stops": (self.exposure_stops, 0.45),
                "grain_scale": (self.grain_scale, 1.0),
                "oversample": (self.oversample, 1),
                "grain_domain_salt": (self.grain_domain_salt, 0),
            }
            changed = [
                f"{name}={actual!r} (baseline {expected!r})"
                for name, (actual, expected) in baseline.items()
                if actual != expected
            ]
            if changed:
                raise ValueError(
                    "V42 research baseline parameters are frozen; use an "
                    "explicit experimental configuration for overrides: "
                    + ", ".join(changed)
                )
        for name in (
            "opencv_threads",
            "binomial_workers",
            "numba_threads",
            "array_workers",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be positive")
        if self.observer_branch_workers not in (1, 2):
            raise ValueError("observer_branch_workers must be 1 or 2")


@dataclass(slots=True)
class ObserverPair:
    """The two accepted observers before an output transfer is applied."""

    projection_linear_rec709: np.ndarray
    scan_linear_rec709: np.ndarray


@dataclass(slots=True)
class EncodedObserverPair:
    projection: np.ndarray
    scan: np.ndarray
    encoding: DeliveryEncoding


@dataclass(slots=True)
class RenderedFrame:
    """One shared stochastic negative viewed through both observer branches."""

    absolute_frame: int
    observers: ObserverPair
    reference_master: EncodedObserverPair
    # Release rendering leaves this empty: the sRGB companion is derived from
    # the encoded professional master, never realized independently here.
    quicktime_companion: EncodedObserverPair | None = None
    # Optional exchange-data authority. Values are RGB printing-density code
    # values in a uint16 container with ten significant bits, not display RGB.
    cineon_printing_density_code: np.ndarray | None = None
    stage_seconds: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.stage_seconds = MappingProxyType(dict(self.stage_seconds))
