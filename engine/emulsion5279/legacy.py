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
import v42_profile as profile  # noqa: E402
import v43h_profile  # noqa: E402
import v44_profile  # noqa: E402
import v45_profile  # noqa: E402
import v48_profile  # noqa: E402
import v49_profile  # noqa: E402
import v50_profile  # noqa: E402
import v51_profile  # noqa: E402
import v52_profile  # noqa: E402
import v53_profile  # noqa: E402
import v54_profile  # noqa: E402
import v55_profile  # noqa: E402
import v56_profile  # noqa: E402
import v57_profile  # noqa: E402
import v58_profile  # noqa: E402
import v59_profile  # noqa: E402
import v60_profile  # noqa: E402
import v61_profile  # noqa: E402
import v62_profile  # noqa: E402
import v63_profile  # noqa: E402
import v64_profile  # noqa: E402
import v66_profile  # noqa: E402
import v72_profile  # noqa: E402
import v46_profile  # noqa: E402
import v48_release_profile  # noqa: E402
import v49_release_profile  # noqa: E402


PROFILES = {
    "v42": profile,
    "v43h": v43h_profile,
    "v44": v44_profile,
    "v45": v45_profile,
    "v48": v48_profile,
    "v49": v49_profile,
    "v50": v50_profile,
    "v51": v51_profile,
    "v52": v52_profile,
    "v53": v53_profile,
    "v54": v54_profile,
    "v55": v55_profile,
    "v56": v56_profile,
    "v57": v57_profile,
    "v58": v58_profile,
    "v59": v59_profile,
    "v60": v60_profile,
    "v61": v61_profile,
    "v62": v62_profile,
    "v63": v63_profile,
    "v64": v64_profile,
    "v66": v66_profile,
    "v72": v72_profile,
    "v46": v46_profile,
    "v48r": v48_release_profile,
    "v49r": v49_release_profile,
}


def profile_for(version: str):
    try:
        return PROFILES[version]
    except KeyError as error:
        raise ValueError(f"unsupported emulsion profile: {version}") from error


def source_fingerprints(active_profile=profile) -> dict[str, str]:
    return {
        "model_sha256": hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),
        "profile_sha256": hashlib.sha256(
            Path(active_profile.__file__).read_bytes()
        ).hexdigest(),
    }
