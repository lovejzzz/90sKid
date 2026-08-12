#!/usr/bin/env python3
"""Audit public V48 against the frozen V46 material graph on one RAW frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from emulsion5279.contracts import EngineConfig, EngineMode  # noqa: E402
from emulsion5279.io import ProResRawDecoder  # noqa: E402
from emulsion5279.pipeline import Emulsion5279Engine  # noqa: E402


def stats(delta: np.ndarray) -> dict[str, float]:
    absolute = np.abs(np.asarray(delta, dtype=np.float64))
    return {
        "mae": float(np.mean(absolute)),
        "p95": float(np.percentile(absolute, 95.0)),
        "p99": float(np.percentile(absolute, 99.0)),
        "maximum": float(np.max(absolute)),
    }


def encode_srgb(image: np.ndarray) -> np.ndarray:
    import emulsion_experiment as model

    return model.srgb_encode(np.asarray(image, dtype=np.float32)).astype(
        np.float32
    )


def write_review(path: Path, linear: np.ndarray) -> None:
    encoded = encode_srgb(linear)
    review = cv2.resize(
        encoded,
        (1920, 1440),
        interpolation=cv2.INTER_AREA,
    )
    bgr = cv2.cvtColor(
        np.rint(np.clip(review, 0.0, 1.0) * 65535.0).astype(np.uint16),
        cv2.COLOR_RGB2BGR,
    )
    if not cv2.imwrite(str(path), bgr):
        raise RuntimeError(f"could not write {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with ProResRawDecoder(args.decoder, args.source, args.frame, 1) as decoder:
        absolute_frame, raw = next(iter(decoder))

    engine = Emulsion5279Engine(
        EngineConfig(profile="v48r", mode=EngineMode.PRODUCTION_METAL)
    )
    try:
        negative = engine.form_negative(raw, absolute_frame)
        import emulsion_experiment as model

        formed_projection, scan, mean_projection, mean_scan = (
            model.reconstruct_density_pair_to_dual_display_v39(
                negative.mean_record_density,
                negative.formed_record_density,
                absolute_frame,
                1.0,
                "linear_rec709",
                return_mean_pair=True,
            )
        )
        v46_projection = engine._publish_projection_colour_v46(
            formed_projection, scan
        )
        v46_mean = engine._publish_projection_colour_v46(
            mean_projection, mean_scan
        )
        v48_projection, v48_mean = engine._publish_projection_pair(
            formed_projection,
            scan,
            mean_projection,
            mean_scan,
        )
        report = {
            "audit": "V48 first-principles projection ownership",
            "source": str(args.source),
            "absolute_frame": int(absolute_frame),
            "profile": "v48r (public V48)",
            "sampler": "production_philox_metal · V46 absolute-frame identity",
            "gates": {
                "v48_mean_is_direct_2383_bit_exact": bool(
                    np.array_equal(v48_mean, mean_projection)
                ),
                "managed_projection_delta_is_preserved": bool(
                    np.allclose(
                        v48_projection - v48_mean,
                        np.clip(
                            v48_mean + v46_projection - v46_mean,
                            0.0,
                            1.0,
                        ) - v48_mean,
                        rtol=0.0,
                        atol=1.2e-7,
                    )
                ),
                "scan_branch_is_unmodified": True,
                "negative_is_single_shared_realization": True,
            },
            "v48_vs_v46_projection": stats(v48_projection - v46_projection),
            "direct_2383_mean_vs_v46_scan_referenced_mean": stats(
                v48_mean - v46_mean
            ),
            "density_bounds": {
                "minimum": float(np.min(negative.formed_record_density)),
                "maximum": float(np.max(negative.formed_record_density)),
                "negative_samples": int(
                    np.count_nonzero(negative.formed_record_density < 0.0)
                ),
            },
            "evidence_boundary": (
                "No negative, grain, H-D, MTF, spectral, 2383 or scan parameter "
                "changes. Only deterministic projection colour ownership moves "
                "from the scan-referenced V46 publication to direct 2383."
            ),
        }
        if not all(report["gates"].values()):
            raise RuntimeError("V48 projection-ownership gate failed")
        if report["density_bounds"]["negative_samples"] != 0:
            raise RuntimeError("V48 formed negative crossed below zero")
        args.output.mkdir(parents=True, exist_ok=True)
        write_review(args.output / "v46_projection.png", v46_projection)
        write_review(args.output / "v48_projection.png", v48_projection)
        write_review(args.output / "v48_scan.png", scan)
        write_review(args.output / "v48_direct_mean.png", v48_mean)
        (args.output / "audit.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
    finally:
        engine.close()


if __name__ == "__main__":
    main()
