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

PRINT_2383_OUTPUT_LATTICE_V45 = Asset(
    name="V45 official-CIE 5279-density to 2383 monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v45.npy",
    sha256="28ac498942c7ddc923fa3b988b8dd6663266026893f96a744b59c8090bfd3cf7",
    required_by_v41_runtime=False,
    authority="generated from Kodak 2383 graphs and official CIE 1931 2-degree 1 nm data",
)

PRINT_2383_OUTPUT_LATTICE_V51 = Asset(
    name="V51 vector-traced-5279 projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v51.npy",
    sha256="7f4cd389d5a329f3582603c49d3bd16cadbdb7fff50639c1365c0a0c6a00cd25",
    required_by_v41_runtime=False,
    authority=(
        "Kodak 5279 vector-traced net-dye and D-min spectra, Kodak 2383 "
        "graphs and official CIE 1931 2-degree 1 nm data"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V53 = Asset(
    name="V53 vector-traced-2383-characteristic projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v53.npy",
    sha256="e8cb27f28a5884cdc709e47fcda45a035cba4f21bf2fbf89414717794ba6bb26",
    required_by_v41_runtime=False,
    authority=(
        "Kodak 5279 vector-traced negative spectra and H-D; Kodak March 2005 "
        "2383 vector-traced Status-A H-D; official CIE 1931 2-degree 1 nm data"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V54 = Asset(
    name="V54 vector-traced-2383-sensitivity projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v54.npy",
    sha256="9d67b8f7c9ba58a1eaf00e61d620b7c34aef4853a8d2bd4ef34f5392a9dc141c",
    required_by_v41_runtime=False,
    authority=(
        "Kodak 5279 vector-traced negative evidence; Kodak March 2005 2383 "
        "vector-traced Status-A H-D and C/M/Y record sensitivity; official CIE"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V55 = Asset(
    name="V55 vector-traced-2383-dye projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v55.npy",
    sha256="d5fe1c9067005a79a47b471c85c8eac0db3cff29138fdeb0a99cf0e7763dfc38",
    required_by_v41_runtime=False,
    authority=(
        "Kodak March 2005 2383 vector-traced Status-A H-D, record sensitivity "
        "and formed-dye absorption spectra; official CIE 1931 observer"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V56 = Asset(
    name="V56 physical-2383-colour-authority projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v56.npy",
    sha256="e09a7d9f8a06f934d621083dc96d74b42bda96f6b8432652842bbdbc8353bd36",
    required_by_v41_runtime=False,
    authority=(
        "V55 official-vector 2383 evidence with physical spectral hue/chroma "
        "authority and the inherited neutral monitor appearance transform"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V57 = Asset(
    name="V57 identity-interimage boundary projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v57.npy",
    sha256="1b22fcfbfb89edbd13d65db9b2362ac9ad8494ea1487cc0bb046f42720684725",
    required_by_v41_runtime=False,
    authority=(
        "V56 physical 2383 colour observer with identity as the explicitly "
        "unidentified minimum-assumption interimage boundary"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V58 = Asset(
    name="V58 integral-LAD-coordinate projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v58.npy",
    sha256="5208603175648fe9aa615065c9731bc9ac29b2955412376ce9688b000227da63",
    required_by_v41_runtime=False,
    authority=(
        "V55 official-vector 2383 evidence with H-61B's simultaneous "
        "integral Status-A LAD resolved into separated H-D coordinates"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V59 = Asset(
    name="V59 visual-neutral-base projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v59.npy",
    sha256="55c7fefe6db0a380e85ce7ea724ceb56f74eca99a95827018229705c9bf17740",
    required_by_v41_runtime=False,
    authority=(
        "V58 integral-LAD coordinate model plus Kodak March 2005 2383 "
        "vector-traced Visual Neutral residual as processed print base/D-min"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V60 = Asset(
    name="V60 D-min-registered-base projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v60.npy",
    sha256="3e13d55aac10971db769d1e2d44fecc421872623c05ea87c06454f7b03e7ed83",
    required_by_v41_runtime=False,
    authority=(
        "V59 Visual Neutral residual spectrum registered to the vector-traced "
        "2383 Status-A H-D minima"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V62 = Asset(
    name="V62 evidence-separated-interimage projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v62.npy",
    sha256="b26660989bc9d5baaa4719e21e9f41a1b9b9d85729ab228316a15914de75b22e",
    required_by_v41_runtime=False,
    authority=(
        "V61 ISO Status-M joint negative inverse and V60 registered 2383 "
        "spectral model, with the unmeasured positive interimage surrogate "
        "withheld and identity declared as the minimum-assumption endpoint"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V63 = Asset(
    name="V63 actual-neutral-trajectory projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v63.npy",
    sha256="ef861a38d840b30fa0dd2b9a6f01b41c8122600daea13e43dcb6ee49bfa67024",
    required_by_v41_runtime=False,
    authority=(
        "V62 evidence-separated negative/print model with the projected gray "
        "calibration derived from its actual neutral 5279-to-2383 trajectory; "
        "off-neutral colour remains scan-referenced and frozen"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V64 = Asset(
    name="V64 published-separated-H-D projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v64.npy",
    sha256="27203fdc8407c446fae65b9f259677cdd8320cdb1ec95961c859105cf211bd32",
    required_by_v41_runtime=False,
    authority=(
        "V63 actual neutral view trajectory with Kodak's vector-traced 2383 "
        "separated-exposure Status-A H-D curves retained directly and the "
        "unmeasured continuous principal-density shaper withdrawn"
    ),
)

PRINT_2383_OUTPUT_LATTICE_V66 = Asset(
    name="V66 Cineon-printing-density projection-monitor lattice",
    path=ENGINE_ROOT / "cache/print_2383_monitor_output_lut_193_v66.npy",
    sha256="03ce9d14a785776121cd33ad76fe7efef222c08a0aee14611f04d10fdb1049ad",
    required_by_v41_runtime=False,
    authority=(
        "V64 evidence-bounded negative/2383 model with the scan-referenced "
        "observer recalibrated to Kodak Cineon printing-density coordinates"
    ),
)

CIE_1931_2DEG_1NM = Asset(
    name="CIE 1931 2-degree standard observer, 1 nm",
    path=ENGINE_ROOT / "references/cie/CIE_xyz_1931_2deg.csv",
    sha256="bd7973e895a97e543815614b19c51ceff552ae9910a424724ae04ed89bd863a3",
    required_by_v41_runtime=False,
    authority="CIE official table; values unchanged, repository line endings normalized",
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

V46_ADAPTIVE_PRINTER_BASE = Asset(
    name="V46 collapsed 129-cube active-set printer atlas",
    path=ENGINE_ROOT / "cache/v46_adaptive_129_power2_base.npy",
    sha256="f889ab074184066608c648c45684619345a7f5a29d6eafe769087d830c8fb1bf",
    required_by_v41_runtime=False,
    authority="exact winning NNLS branch at each power-2 Status-M lattice node",
)

V46_ADAPTIVE_PRINTER_ACTIVE_RISK = Asset(
    name="V46 active-set boundary cell map",
    path=ENGINE_ROOT / "cache/v46_adaptive_129_power2_active_risk.npy",
    sha256="a3654fbf4440a87954b6c2d7f8f21e63c45b77c56c984eb66a0979c6c6b0bdfe",
    required_by_v41_runtime=False,
    authority="derived from exact active-set winners at the eight parent-cell corners",
)

V46_ADAPTIVE_PRINTER_AXIS = Asset(
    name="V46 power-2 Status-M density axis",
    path=ENGINE_ROOT / "cache/v46_adaptive_129_power2_axis.npy",
    sha256="697e0be23f9bb9c959d16a56da1bcd1926a9515bc09e4e1a75748bf3b4aeb334",
    required_by_v41_runtime=False,
    authority="generated nonuniform density coordinate, 0 to 5.5 D",
)

V46_ADAPTIVE_PRINTER_CELLS = Asset(
    name="V46 real-footage-demanded microbrick cell index",
    path=ENGINE_ROOT / "cache/v46_adaptive_129_power2_cells.npy",
    sha256="3ba8087a89374bfa563fefb5929d9ade8f20d723fa906dbbde428341289ec7d2",
    required_by_v41_runtime=False,
    authority="exact runtime risk predicate over T020, T032 and T007 witness frames",
)

V46_ADAPTIVE_PRINTER_BLOCKS = Asset(
    name="V46 KKT-certified 5-cube spectral microbricks",
    path=ENGINE_ROOT / "cache/v46_adaptive_129_power2_blocks.npy",
    sha256="e419d085a67a11eebda8a336e5340956e6d9113e8b50f51ecae236136b3f61bd",
    required_by_v41_runtime=False,
    authority="deduplicated local exact NNLS solves with per-node KKT fallback",
)


def verify_v41_runtime_assets() -> None:
    for asset in (PRINT_2383_OUTPUT_LATTICE,):
        asset.verify()


def verify_v46_runtime_assets() -> None:
    for asset in (
        V46_ADAPTIVE_PRINTER_BASE,
        V46_ADAPTIVE_PRINTER_ACTIVE_RISK,
        V46_ADAPTIVE_PRINTER_AXIS,
        V46_ADAPTIVE_PRINTER_CELLS,
        V46_ADAPTIVE_PRINTER_BLOCKS,
    ):
        asset.verify()


def projection_lattice_for_profile(profile: str) -> Asset:
    if profile in {"v46", "v48r", "v49r", "v66", "v72"}:
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V66.verify()
        return PRINT_2383_OUTPUT_LATTICE_V66
    if profile == "v64":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V64.verify()
        return PRINT_2383_OUTPUT_LATTICE_V64
    if profile == "v63":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V63.verify()
        return PRINT_2383_OUTPUT_LATTICE_V63
    if profile == "v62":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V62.verify()
        return PRINT_2383_OUTPUT_LATTICE_V62
    if profile in {"v60", "v61"}:
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V60.verify()
        return PRINT_2383_OUTPUT_LATTICE_V60
    if profile == "v59":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V59.verify()
        return PRINT_2383_OUTPUT_LATTICE_V59
    if profile == "v58":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V58.verify()
        return PRINT_2383_OUTPUT_LATTICE_V58
    if profile == "v57":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V57.verify()
        return PRINT_2383_OUTPUT_LATTICE_V57
    if profile == "v56":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V56.verify()
        return PRINT_2383_OUTPUT_LATTICE_V56
    if profile == "v55":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V55.verify()
        return PRINT_2383_OUTPUT_LATTICE_V55
    if profile == "v54":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V54.verify()
        return PRINT_2383_OUTPUT_LATTICE_V54
    if profile == "v53":
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V53.verify()
        return PRINT_2383_OUTPUT_LATTICE_V53
    if profile in {"v51", "v52"}:
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V51.verify()
        return PRINT_2383_OUTPUT_LATTICE_V51
    if profile in {"v45", "v48", "v49", "v50"}:
        CIE_1931_2DEG_1NM.verify()
        PRINT_2383_OUTPUT_LATTICE_V45.verify()
        return PRINT_2383_OUTPUT_LATTICE_V45
    PRINT_2383_OUTPUT_LATTICE.verify()
    return PRINT_2383_OUTPUT_LATTICE


def verify_research_assets() -> None:
    for asset in (
        PRINT_2383_OUTPUT_LATTICE,
        PRINT_2383_OUTPUT_LATTICE_V45,
        PRINT_2383_OUTPUT_LATTICE_V51,
        PRINT_2383_OUTPUT_LATTICE_V53,
        PRINT_2383_OUTPUT_LATTICE_V54,
        PRINT_2383_OUTPUT_LATTICE_V55,
        PRINT_2383_OUTPUT_LATTICE_V56,
        PRINT_2383_OUTPUT_LATTICE_V57,
        PRINT_2383_OUTPUT_LATTICE_V58,
        PRINT_2383_OUTPUT_LATTICE_V59,
        PRINT_2383_OUTPUT_LATTICE_V60,
        PRINT_2383_OUTPUT_LATTICE_V62,
        PRINT_2383_OUTPUT_LATTICE_V63,
        PRINT_2383_OUTPUT_LATTICE_V64,
        PRINT_2383_OUTPUT_LATTICE_V66,
        CIE_1931_2DEG_1NM,
        PANASONIC_V709,
        PANASONIC_RAW_GAMUT,
    ):
        asset.verify()
