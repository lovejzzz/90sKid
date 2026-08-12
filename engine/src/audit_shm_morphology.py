#!/usr/bin/env python3
"""Audit SHM morphology against independently measured Silver Efex envelopes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fsd_density import (
    _lookup_binomial_density,
    binomial_quantile_table,
    tone_taper,
)
from shm_density import (
    DEFAULT_PROFILE,
    morphology_uniform_field,
    trix_reference_tone_gain,
)


MEASURED_PATCH_ENVELOPE = {
    "lag1": [0.2421, 0.4157],
    "skew": [-0.3998, 0.1630],
    "excess_kurtosis": [-0.2190, 0.5673],
    "source": (
        "read-only measurements of five locally installed Silver Efex B&W "
        "stock resources; bounds are validation references, not copied assets"
    ),
}


def _smooth_power_ratio_cv(field: np.ndarray, block: int = 128) -> float:
    values: list[float] = []
    height = field.shape[0] // block * block
    width = field.shape[1] // block * block
    fy = np.fft.fftfreq(block)[:, None]
    fx = np.fft.rfftfreq(block)[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    low = (radius > 0.035) & (radius < 0.12)
    high = (radius > 0.22) & (radius < 0.42)
    for y0 in range(0, height, block):
        for x0 in range(0, width, block):
            transform = np.fft.rfft2(field[y0 : y0 + block, x0 : x0 + block])
            power = np.abs(transform) ** 2
            values.append(float(power[high].mean() / max(power[low].mean(), 1e-12)))
    array = np.asarray(values, dtype=np.float64)
    return float(array.std() / array.mean())


def measure(field: np.ndarray) -> dict[str, float]:
    centered = field.astype(np.float64) - float(field.mean(dtype=np.float64))
    variance = float(np.mean(centered * centered))
    x1 = float(np.mean(centered[:, :-1] * centered[:, 1:]) / variance)
    y1 = float(np.mean(centered[:-1] * centered[1:]) / variance)
    return {
        "mean": float(centered.mean()),
        "standard_deviation": float(np.sqrt(variance)),
        "lag1_x": x1,
        "lag1_y": y1,
        "lag1_mean": (x1 + y1) * 0.5,
        "lag1_anisotropy": abs(x1 - y1),
        "skew": float(np.mean(centered**3) / variance**1.5),
        "excess_kurtosis": float(np.mean(centered**4) / variance**2 - 3.0),
        "local_spectral_ratio_cv": _smooth_power_ratio_cv(centered),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", type=int, default=1536)
    parser.add_argument("--frame", type=int, default=17)
    args = parser.parse_args()
    controlled = {
        "shadow": {
            "tone": 0.08833448, "lag1": 0.38101635,
            "skew": 0.13084918, "excess_kurtosis": 0.36073144,
        },
        "mid": {
            "tone": 0.53167010, "lag1": 0.38462828,
            "skew": 0.12873554, "excess_kurtosis": 0.36940639,
        },
        "highlight": {
            "tone": 0.91166552, "lag1": 0.38775263,
            "skew": 0.12319859, "excess_kurtosis": 0.32429689,
        },
    }
    table = binomial_quantile_table(DEFAULT_PROFILE.site_count)
    rows: dict[str, dict[str, float]] = {}
    for label, target in controlled.items():
        tone = np.full(
            (args.size, args.size), target["tone"], dtype=np.float32
        )
        uniform = morphology_uniform_field(
            args.size, args.size, args.frame, DEFAULT_PROFILE, tone
        )
        candidate = _lookup_binomial_density(tone, uniform, table)
        formed_residual = (
            tone_taper(tone)
            * trix_reference_tone_gain(tone)
            * (candidate - tone)
        )
        rows[label] = {
            **measure(formed_residual),
            "controlled_tone": target["tone"],
            "target_lag1": target["lag1"],
            "target_skew": target["skew"],
            "target_excess_kurtosis": target["excess_kurtosis"],
        }
    lag = [row["lag1_mean"] for row in rows.values()]
    skew = [row["skew"] for row in rows.values()]
    kurtosis = [row["excess_kurtosis"] for row in rows.values()]
    gates = {
        "isotropic": max(row["lag1_anisotropy"] for row in rows.values()) < 0.01,
        "no_false_tone_scale_breathing": max(lag) - min(lag) < 0.03,
        "inside_measured_lag_envelope": (
            min(lag) >= MEASURED_PATCH_ENVELOPE["lag1"][0]
            and max(lag) <= MEASURED_PATCH_ENVELOPE["lag1"][1]
        ),
        "controlled_trix_lag_fit": max(
            abs(rows[label]["lag1_mean"] - controlled[label]["lag1"])
            for label in rows
        ) < 0.02,
        "controlled_trix_skew_fit": max(
            abs(rows[label]["skew"] - controlled[label]["skew"])
            for label in rows
        ) < 0.08,
        "controlled_trix_kurtosis_fit": max(
            abs(
                rows[label]["excess_kurtosis"]
                - controlled[label]["excess_kurtosis"]
            )
            for label in rows
        ) < 0.14,
        "non_gaussian_thick_tail_organization": min(kurtosis) > 0.18,
        "locally_nonstationary_spectrum": min(
            row["local_spectral_ratio_cv"] for row in rows.values()
        ) > 0.04,
    }
    report = {
        "audit": "Silver-Halide Morphology statistical validation",
        "status": (
            "independent same-class morphology; not a pixel-identical DxO/Nik "
            "replica and not a measured 5279 model"
        ),
        "profile": DEFAULT_PROFILE.__dict__,
        "measured_patch_envelope": MEASURED_PATCH_ENVELOPE,
        "controlled_trix_targets": controlled,
        "tone_fields": rows,
        "gates": gates,
        "all_gates_pass": all(gates.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_gates_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
