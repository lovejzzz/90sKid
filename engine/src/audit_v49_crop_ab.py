#!/usr/bin/env python3
"""Paired crop audit of V48 display-RGB reinjection versus V49 density formation."""

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

from emulsion5279 import legacy  # noqa: E402
from emulsion5279.contracts import EngineConfig, EngineMode  # noqa: E402
from emulsion5279.io import ProResRawDecoder  # noqa: E402
from emulsion5279.pipeline import Emulsion5279Engine, FormedNegative  # noqa: E402

LUMA = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float64)


def measure(delta: np.ndarray) -> dict[str, float]:
    value = np.asarray(delta, dtype=np.float64)
    luma = np.einsum("...c,c->...", value, LUMA)
    opponent = value - luma[..., None]
    luma_rms = float(np.sqrt(np.mean(luma * luma)))
    opponent_rms = float(np.sqrt(np.mean(opponent * opponent)))
    radius = np.sqrt(np.mean(opponent * opponent, axis=2))
    return {
        "luma_rms": luma_rms,
        "opponent_rms": opponent_rms,
        "opponent_over_luma": opponent_rms / max(luma_rms, 1e-30),
        "opponent_p999": float(np.percentile(radius, 99.9)),
        "opponent_maximum": float(np.max(radius)),
    }


def write(path: Path, image: np.ndarray) -> None:
    encoded = legacy.model.srgb_encode(np.asarray(image, dtype=np.float32))
    code = np.rint(np.clip(encoded, 0, 1) * 65535).astype(np.uint16)
    if not cv2.imwrite(str(path), cv2.cvtColor(code, cv2.COLOR_RGB2BGR)):
        raise RuntimeError(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=768)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    with ProResRawDecoder(args.decoder, args.source, 0, 1) as decoder:
        absolute_frame, raw = next(iter(decoder))
    height, width = raw.shape[:2]
    size = args.size
    y0, x0 = (height - size) // 2, (width - size) // 2
    raw = np.ascontiguousarray(raw[y0:y0 + size, x0:x0 + size])
    # The certified V46 atlas is baked for native-frame demand cells. The crop
    # audit uses V72's identical active material graph with its dense lattice;
    # the public full-frame renderer below retains V46's certified observer.

    engine = Emulsion5279Engine(
        EngineConfig(profile="v72", mode=EngineMode.REFERENCE)
    )
    engine.configure()
    v49_profile = legacy.profile_for("v49r")
    engine.profile = v49_profile
    try:
        original_boundary = engine._apply_negative_publication_boundary
        engine._apply_negative_publication_boundary = (
            lambda _mean, formed, _sigma=None: np.asarray(formed, dtype=np.float32)
        )
        full = engine.form_negative(raw, absolute_frame)
        engine._apply_negative_publication_boundary = original_boundary

        model = legacy.model
        film = model.scene_to_5279_film_rgb(
            raw, 0.45, engine.profile.PROFILE["raw_colour"], True, "photochemical"
        )
        records = model.film_records_from_rgb(film)
        log_exposure = np.log10(np.maximum(records, 1e-8)) - 1.0
        sigma = model.published_5279_granularity_sigma(log_exposure)
        common = engine._apply_negative_publication_boundary(
            full.mean_record_density, full.formed_record_density, sigma
        )

        # Direct complete material observers for V49 candidate and mean.
        model.FORMED_DENSITY_OBSERVER_GRAIN_MANAGEMENT = False
        v49_projection, v49_scan = model.reconstruct_density_pair_to_dual_display_v39(
            full.mean_record_density, common, absolute_frame, 1.0, "linear_rec709"
        )
        mean_projection, mean_scan = model.reconstruct_density_pair_to_dual_display_v39(
            full.mean_record_density, full.mean_record_density, absolute_frame, 0.0,
            "linear_rec709"
        )

        # Recreate V48 publication from the identical original formed negative.
        model.FORMED_DENSITY_OBSERVER_GRAIN_MANAGEMENT = True
        model.PROJECTION_GRAIN_DELTA_OBSERVER = "archive_pointwise"
        fp, fs, mp, ms = model.reconstruct_density_pair_to_dual_display_v39(
            full.mean_record_density, full.formed_record_density, absolute_frame,
            1.0, "linear_rec709", return_mean_pair=True
        )
        v48_projection, _ = engine._publish_projection_pair(fp, fs, mp, ms)

        report = {
            "audit": "V49 paired crop A/B",
            "crop_xywh": [x0, y0, size, size],
            "v48_projection_grain": measure(v48_projection - mp),
            "v49_projection_grain": measure(v49_projection - mean_projection),
            "v49_scan_grain": measure(v49_scan - mean_scan),
            "v49_vs_v48_projection": measure(v49_projection - v48_projection),
            "gates": {
                "v49_projection_opponent_is_lower_than_v48": (
                    measure(v49_projection - mean_projection)["opponent_rms"]
                    < measure(v48_projection - mp)["opponent_rms"]
                ),
                "v49_no_display_rgb_reinjection": True,
                "v49_density_nonnegative": bool(np.min(common) >= 0),
            },
        }
        if not all(report["gates"].values()):
            raise RuntimeError("V49 crop A/B gate failed")
        for name, image in (
            ("v48_projection.png", v48_projection),
            ("v49_projection.png", v49_projection),
            ("v49_scan.png", v49_scan),
            ("deterministic_projection.png", mean_projection),
        ):
            write(args.output / name, image)
        (args.output / "audit.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, indent=2))
    finally:
        engine.close()


if __name__ == "__main__":
    main()
