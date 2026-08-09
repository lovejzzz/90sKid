"""Narrow adapter around the validated V41 monolith.

Only this module knows that the historical sources use top-level imports and
module-owned caches.  New engine code talks to a configured backend instance.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys


LEGACY_SRC = Path(__file__).resolve().parents[1] / "src"
if str(LEGACY_SRC) not in sys.path:
    sys.path.insert(0, str(LEGACY_SRC))

import emulsion_experiment as model  # noqa: E402
import v41_profile as profile  # noqa: E402


def source_fingerprints() -> dict[str, str]:
    return {
        "model_sha256": hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),
        "profile_sha256": hashlib.sha256(Path(profile.__file__).read_bytes()).hexdigest(),
    }
