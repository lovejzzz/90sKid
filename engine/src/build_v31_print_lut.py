#!/usr/bin/env python3
"""Build the exact 193-cube V31 placement-probe cache.

This research cache is retained for reproducibility but is not the accepted
V31 release transform; see ``apply_v31_normal_process_adapter.py``.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np

import emulsion_experiment as e
import v31_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    v31_profile.apply(e)
    lattice = e.build_2383_monitor_output_lut(size=193)
    if lattice.shape != (193, 193, 193, 3) or lattice.dtype != np.float32:
        raise RuntimeError("unexpected V31 projection lattice")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.output, lattice, allow_pickle=False)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    print(digest, flush=True)


if __name__ == "__main__":
    main()
