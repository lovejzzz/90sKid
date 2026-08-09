"""Integrity-checked external and generated assets used by the engine."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


ENGINE_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Asset:
    name: str
    path: Path
    sha256: str
    required_by_v41_runtime: bool
    authority: str

    def verify(self) -> None:
        if not self.path.is_file():
            raise FileNotFoundError(f"missing {self.name}: {self.path}")
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        if digest != self.sha256:
            raise ValueError(
                f"{self.name} integrity mismatch: expected {self.sha256}, got {digest}"
            )


PRINT_2383_OUTPUT_LATTICE = Asset(
    name="V30 analytical 5279-density to 2383 monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v30.npy",
    sha256="5a7d99c9e50a9816205a3ecc06e4adc81f520fb3baa6f0aeba6f351093a4f98c",
    required_by_v41_runtime=True,
    authority="generated from the analytical Kodak 2383 observer",
)

PANASONIC_V709 = Asset(
    name="Panasonic V-Log to V-709 diagnostic LUT",
    path=ENGINE_ROOT / "references/panasonic_v709/VLog_to_V709_forV35_ver100.cube",
    sha256="f99223675b29933952da2153bdb3137dd749d12964d0753db85e47576ca4578d",
    required_by_v41_runtime=False,
    authority="Panasonic official download; diagnostic display witness only",
)

PANASONIC_RAW_GAMUT = Asset(
    name="Panasonic RAW Gamut to V-Gamut camera LUT",
    path=ENGINE_ROOT / "references/VLog_RAWGamut_to_VLog_VGamut_forS1H_ver100.cube",
    sha256="bd75a87cc8664566edbcfee5af88851e5840a720e27e92a2f4267d9d935dd062",
    required_by_v41_runtime=False,
    authority="Panasonic official download; legacy RAW-Gamut decoder path only",
)


def verify_v41_runtime_assets() -> None:
    for asset in (PRINT_2383_OUTPUT_LATTICE,):
        asset.verify()


def verify_research_assets() -> None:
    for asset in (PRINT_2383_OUTPUT_LATTICE, PANASONIC_V709, PANASONIC_RAW_GAMUT):
        asset.verify()
