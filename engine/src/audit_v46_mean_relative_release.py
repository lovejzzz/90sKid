#!/usr/bin/env python3
"""V46 release gate for stochastic colour tails, separated from scene detail.

The historical whole-picture colour-tail gate is retained as a diagnostic, but
it is not a valid grain test: deterministic one-pixel chromatic detail can fail
it.  This audit reconstructs the deterministic observer from the same V46
negative, sends it through the same maximum-budget sRGB ProRes XQ path, and
measures only the delivered formed-minus-mean residual.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from audit_v63_neutral_trajectory import difference_metrics
from audit_v77_frequency_and_projection_grain_observer import (
    decode_srgb_movie,
    measure_mean_relative_grain_tail,
)
from emulsion5279.contracts import EngineConfig, EngineMode
from emulsion5279.io import (
    ProResRawDecoder,
    _xq_command,
    rebuild_srgb_companion_from_master,
)
from emulsion5279 import legacy
from emulsion5279.pipeline import Emulsion5279Engine


BRANCHES = {
    "projection": "projection",
    "scan": "bluray_scan",
}


def encode_decode_authoritative_companion(
    linear: np.ndarray,
    root: Path,
    label: str,
    fps: str,
) -> np.ndarray:
    """Round-trip exactly as production: BT.1886 master, then sRGB companion."""

    height, width = linear.shape[:2]
    master = root / f"{label}-master.mov"
    companion = root / f"{label}-companion.mov"
    code = legacy.model.bt1886_reference_encode(linear).astype(np.float32)
    payload = np.rint(np.clip(code, 0.0, 1.0) * 65535.0).astype(
        "<u2", copy=False
    )
    completed = subprocess.run(
        _xq_command(master, width, height, fps),
        input=payload.tobytes(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode("utf-8", "replace"))
    legacy.model.finalize_prores_rec709_metadata(master)
    rebuild_srgb_companion_from_master(master, companion, 1)
    decoded = decode_srgb_movie(companion, width, height)
    master.unlink(missing_ok=True)
    companion.unlink(missing_ok=True)
    (root / "still_emulsion.jpg").unlink(missing_ok=True)
    return decoded


def measure(
    input_path: Path,
    release_root: Path,
    decoder_path: Path,
    *,
    frame: int,
) -> dict[str, object]:
    config = EngineConfig(
        profile="v46",
        exposure_stops=0.45,
        grain_scale=1.0,
        oversample=1,
        mode=EngineMode.PRODUCTION_METAL,
        opencv_threads=8,
        binomial_workers=8,
        numba_threads=8,
        array_workers=8,
        observer_branch_workers=1,
        research_baseline=True,
    )
    engine = Emulsion5279Engine(config)
    engine.configure()
    try:
        with ProResRawDecoder(decoder_path, input_path, frame, 1) as decoder:
            absolute_frame, raw = next(iter(decoder))
            fps = decoder.fps
        negative = engine.form_negative(raw, absolute_frame)
        formed, mean = engine.observe_with_mean(negative, absolute_frame)
    finally:
        engine.close()

    report: dict[str, object] = {
        "audit": "V46 paired deterministic-mean stochastic colour-tail gate",
        "profile": "v46",
        "input": str(input_path),
        "absolute_frame": int(absolute_frame),
        "method": (
            "decode delivered sRGB ProRes XQ formed frame; independently encode "
            "the same-path deterministic mean through the identical XQ command; "
            "measure formed-minus-mean in sRGB"
        ),
        "historical_gate_status": (
            "whole-picture colour-tail statistics are diagnostic only because "
            "they include deterministic scene detail"
        ),
        "branches": {},
    }
    passed = True
    with tempfile.TemporaryDirectory(prefix="v46-mean-relative-") as temporary:
        temporary_path = Path(temporary)
        for branch, directory in BRANCHES.items():
            formed_linear = (
                formed.projection_linear_rec709
                if branch == "projection"
                else formed.scan_linear_rec709
            )
            mean_linear = (
                mean.projection_linear_rec709
                if branch == "projection"
                else mean.scan_linear_rec709
            )
            recomputed_formed = encode_decode_authoritative_companion(
                formed_linear,
                temporary_path,
                f"{branch}-formed",
                fps,
            )
            encoded_mean = encode_decode_authoritative_companion(
                mean_linear,
                temporary_path,
                f"{branch}-mean",
                fps,
            )
            delivered_path = (
                release_root
                / directory
                / "06_quicktime_preview_srgb_prores4444.mov"
            )
            delivered_formed = decode_srgb_movie(
                delivered_path,
                formed_linear.shape[1],
                formed_linear.shape[0],
            )
            delivered_parity = difference_metrics(
                recomputed_formed,
                delivered_formed,
            )
            tail = measure_mean_relative_grain_tail(
                delivered_formed,
                encoded_mean,
            )
            gates = {
                # Independent XQ encodes are allowed quantizer-level changes,
                # but the recomputed image must remain visually/numerically the
                # same delivery.
                "delivered_reproduction_linear_mae_le_5e_4": bool(
                    delivered_parity["linear_rgb_mae"] <= 5e-4
                ),
                "median_opponent_p9999_le_0_07": bool(
                    tail["median_opponent_p9999"] <= 0.07
                ),
                "isolated_gt_0_08_zero": bool(
                    tail["isolated_gt_0_08_count"] == 0
                ),
            }
            if branch == "projection":
                # The projection's old whole-picture P99.99 assertion is one
                # of the three confounded gates this paired test replaces.
                gates["opponent_p9999_le_0_07"] = bool(
                    tail["opponent_p9999"] <= 0.07
                )
            branch_pass = all(gates.values())
            passed &= branch_pass
            report["branches"][branch] = {
                "delivered_path": str(delivered_path),
                "delivered_reproduction": delivered_parity,
                "mean_relative_grain_tail": tail,
                "gates": gates,
                "pass": branch_pass,
            }
    report["all_gates_pass"] = passed
    report["decision"] = (
        "The paired stochastic gate replaces only the confounded whole-picture "
        "colour-tail assertions; metadata, transfer, frame-count, tone, and all "
        "other native release gates remain mandatory."
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("release_root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decoder", type=Path, default=Path("/tmp/prores_raw_float_decode"))
    parser.add_argument("--frame", type=int, default=0)
    args = parser.parse_args()
    report = measure(
        args.input,
        args.release_root,
        args.decoder,
        frame=args.frame,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_gates_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
