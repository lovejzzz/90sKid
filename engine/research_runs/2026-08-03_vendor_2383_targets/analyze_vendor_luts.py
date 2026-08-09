#!/usr/bin/env python3
"""Compare local colour coupling in independently supplied Kodak 2383 looks.

The comparison deliberately uses row-normalized derivatives of log output at a
neutral input.  Those ratios are unchanged by a shared scalar input transfer
curve and by per-output-channel scalar derivatives, so they remain useful when
the vendors do not document identical absolute input/output encodings.
"""

from __future__ import annotations

import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
SOURCES = {
    "resolve_rec709_d55": Path(
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Film Looks/Rec709 Kodak 2383 D55.cube"
    ),
    "resolve_rec709_d60": Path(
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Film Looks/Rec709 Kodak 2383 D60.cube"
    ),
    "resolve_rec709_d65": Path(
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/Film Looks/Rec709 Kodak 2383 D65.cube"
    ),
    "adobe_5218_2383": Path(
        "/Applications/Adobe Photoshop 2026/Presets/3DLUTs/Kodak 5218 Kodak 2383 (by Adobe).cube"
    ),
    "filmvision_sd1": Path(
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/FilmVision Pro/Print/I- Standard/Print SD1 Kodak 2383.cube"
    ),
    "filmvision_sd2": Path(
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/FilmVision Pro/Print/I- Standard/Print SD2 Kodak 2383.cube"
    ),
    "filmvision_sd3": Path(
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/FilmVision Pro/Print/I- Standard/Print SD3 Kodak 2383.cube"
    ),
    "bmd_aces_lmt": Path(
        "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/LMT Kodak 2383 Print Emulation.xml"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cube(path: Path) -> np.ndarray:
    size = None
    values: list[list[float]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("LUT_3D_SIZE"):
            size = int(line.split()[1])
            continue
        if line.startswith(("TITLE", "DOMAIN_", "LUT_3D_INPUT_RANGE")):
            continue
        fields = line.split()
        if len(fields) == 3:
            values.append([float(v) for v in fields])
    if size is None or len(values) != size**3:
        raise ValueError(f"invalid cube {path}: size={size}, values={len(values)}")
    # Standard .cube ordering is red-fastest, hence [blue, green, red].
    return np.asarray(values, dtype=np.float64).reshape(size, size, size, 3)


def sample_3d(lut: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(rgb, dtype=np.float64), 0.0, 1.0)
    p = x * (lut.shape[0] - 1)
    lo = np.floor(p).astype(int)
    hi = np.minimum(lo + 1, lut.shape[0] - 1)
    f = p - lo
    r0, g0, b0 = lo
    r1, g1, b1 = hi
    fr, fg, fb = f
    c000 = lut[b0, g0, r0]
    c100 = lut[b0, g0, r1]
    c010 = lut[b0, g1, r0]
    c110 = lut[b0, g1, r1]
    c001 = lut[b1, g0, r0]
    c101 = lut[b1, g0, r1]
    c011 = lut[b1, g1, r0]
    c111 = lut[b1, g1, r1]
    c00 = c000 * (1 - fr) + c100 * fr
    c10 = c010 * (1 - fr) + c110 * fr
    c01 = c001 * (1 - fr) + c101 * fr
    c11 = c011 * (1 - fr) + c111 * fr
    return (c00 * (1 - fg) + c10 * fg) * (1 - fb) + (
        c01 * (1 - fg) + c11 * fg
    ) * fb


def parse_floats(text: str | None) -> np.ndarray:
    if not text:
        raise ValueError("missing array text")
    return np.asarray([float(x) for x in text.split()], dtype=np.float64)


class BmdAcesLmt:
    """Minimal evaluator for the transform sequence in BMD's bundled CLF."""

    def __init__(self, path: Path):
        tree = ET.parse(path)
        root = tree.getroot()
        ns = {"c": root.tag.split("}")[0].strip("{")}
        children = list(root)
        matrix_nodes = [x for x in children if x.tag.endswith("Matrix")]
        self.ap0_to_xyz = parse_floats(matrix_nodes[0].find("c:Array", ns).text).reshape(3, 3)
        self.xyz_to_p3 = parse_floats(matrix_nodes[1].find("c:Array", ns).text).reshape(3, 3)
        lut1_node = next(x for x in children if x.tag.endswith("LUT1D"))
        lut3_node = next(x for x in children if x.tag.endswith("LUT3D"))
        self.xyz_to_ap0 = parse_floats(matrix_nodes[-1].find("c:Array", ns).text).reshape(3, 3)
        self.lut1 = parse_floats(lut1_node.find("c:Array", ns).text).reshape(514, 3)
        # CLF serializes blue fastest (unlike .cube, which is red fastest).
        # Convert CLF [red, green, blue] axes to sample_3d's [blue, green, red].
        self.lut3 = (
            parse_floats(lut3_node.find("c:Array", ns).text)
            .reshape(33, 33, 33, 3)
            .transpose(2, 1, 0, 3)
        )

    @staticmethod
    def _cdl_saturation(rgb: np.ndarray, saturation: float = 1.4) -> np.ndarray:
        # ASC CDL v1.2 luma coefficients.
        luma = float(np.dot(rgb, [0.2126, 0.7152, 0.0722]))
        return luma + saturation * (rgb - luma)

    def _sample_1d(self, rgb: np.ndarray) -> np.ndarray:
        p = np.clip(rgb, 0.0, 1.0) * (len(self.lut1) - 1)
        lo = np.floor(p).astype(int)
        hi = np.minimum(lo + 1, len(self.lut1) - 1)
        f = p - lo
        return self.lut1[lo, np.arange(3)] * (1 - f) + self.lut1[
            hi, np.arange(3)
        ] * f

    def __call__(self, ap0: np.ndarray) -> np.ndarray:
        # CLF Matrix arrays multiply column vectors.
        p3 = self.xyz_to_p3 @ (self.ap0_to_xyz @ np.asarray(ap0, dtype=np.float64))
        p3 = np.clip(p3 / 100.0, 0.0, 1.0)
        p3 = self._cdl_saturation(p3)
        shaped = self._sample_1d(p3)
        xyz = sample_3d(self.lut3, shaped)
        return np.maximum(self.xyz_to_ap0 @ xyz, 0.0)


def jacobian_log_output(fn, neutral: float, step: float = 1e-4) -> tuple[np.ndarray, np.ndarray]:
    x = np.full(3, neutral, dtype=np.float64)
    base = np.maximum(fn(x), 1e-8)
    jac = np.empty((3, 3), dtype=np.float64)
    for c in range(3):
        xp, xm = x.copy(), x.copy()
        xp[c] += step
        xm[c] -= step
        yp = np.log(np.maximum(fn(xp), 1e-8))
        ym = np.log(np.maximum(fn(xm), 1e-8))
        jac[:, c] = (yp - ym) / (2 * step)
    normalized = jac / np.diag(jac)[:, None]
    return base, normalized


def neutral_for_output(fn, target_geomean: float, domain_max: float = 1.0) -> float:
    if domain_max > 1.0:
        candidates = np.geomspace(1e-6, domain_max, 8000)
    else:
        candidates = np.linspace(0.001, domain_max, 4000)
    geomeans = np.asarray(
        [math.exp(float(np.mean(np.log(np.maximum(fn(np.full(3, x)), 1e-8))))) for x in candidates]
    )
    return float(candidates[np.argmin(np.abs(geomeans - target_geomean))])


def main() -> None:
    functions = {name: (lambda x, lut=load_cube(path): sample_3d(lut, x)) for name, path in SOURCES.items() if path.suffix == ".cube"}
    functions["bmd_aces_lmt"] = BmdAcesLmt(SOURCES["bmd_aces_lmt"])

    targets = [0.18, 0.35, 0.50, 0.70]
    result: dict[str, object] = {
        "method": "finite-difference Jacobian of log(output), each row divided by its diagonal; invariant to shared scalar input encoding and per-channel scalar output encoding derivatives",
        "sources": {name: {"path": str(path), "sha256": sha256(path)} for name, path in SOURCES.items()},
        "looks": {},
    }
    for name, fn in functions.items():
        domain_max = 100.0 if name == "bmd_aces_lmt" else 1.0
        rows = []
        for target in targets:
            neutral = neutral_for_output(fn, target, domain_max=domain_max)
            step = max(1e-5, neutral * 1e-4)
            output, jac = jacobian_log_output(fn, neutral, step=step)
            rows.append(
                {
                    "target_output_geomean": target,
                    "neutral_input": neutral,
                    "neutral_output": output.tolist(),
                    "row_normalized_log_jacobian": jac.tolist(),
                }
            )
        result["looks"][name] = rows

    (ROOT / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
