"""V35 performance release: unchanged baseline model, validated new execution graph."""

from __future__ import annotations

import v34_profile


PROFILE = {
    **v34_profile.PROFILE,
    "name": "V35 · 5279 Baseline · validated Production graph",
    "short_name": "V35",
    "version_id": "v35",
    "image_change_from_v34": (
        "No colour, contrast, black, gamma, MTF, DIR, grain amplitude or grain "
        "spectrum retune. Production uses a statistically equivalent independent "
        "Philox-u32 Bernoulli finite-site realization and float32 spatial storage."
    ),
    "pipeline_change": (
        "Asynchronous no-copy Metal finite-site sampling overlaps CPU filtering; "
        "the V31 boundary reuses full-frame buffers. Observers remain serial "
        "because the installed Numba workqueue is not concurrency-safe; Archive "
        "exact remains the V34 CPU graph."
    ),
}


def apply(module) -> None:
    v34_profile.apply(module)
