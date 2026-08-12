#!/usr/bin/env python3
"""Combine V46 native, paired-tail, delivery and numerical certification gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SUPERSEDED_GATES = {
    ("T020", "projection", "median_opponent_p9999_le_0_05"),
    ("T020", "projection", "isolated_gt_0_06_poisson_fwer"),
    ("T020", "projection", "dark_opponent_p9999_le_0_035"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--precision",
        type=Path,
        default=Path("engine/research_runs/v46_adaptive_real_frame_precision.json"),
    )
    parser.add_argument(
        "--coverage",
        type=Path,
        default=Path("engine/research_runs/v46_pipeline_stage_cache_coverage_final.json"),
    )
    args = parser.parse_args()

    native = json.loads((args.root / "v46_release_audit.json").read_text())
    paired = json.loads(
        (args.root / "v46_mean_relative_release_audit.json").read_text()
    )
    delivery = json.loads((args.root / "v46_delivery_audit.json").read_text())
    precision = json.loads(args.precision.read_text())
    coverage = json.loads(args.coverage.read_text())

    unexpected_failures: list[list[str]] = []
    observed_superseded: list[list[str]] = []
    for scene, scene_record in native["scenes"].items():
        for branch, branch_record in scene_record.items():
            for gate, value in branch_record["gates"].items():
                if value:
                    continue
                identity = (scene, branch, gate)
                if identity in SUPERSEDED_GATES:
                    observed_superseded.append(list(identity))
                else:
                    unexpected_failures.append(list(identity))

    precision_pass = bool(
        precision.get(
            "all_quality_gates_pass",
            precision.get("all_gates_pass", precision.get("pass", False)),
        )
    )
    coverage_pass = bool(
        coverage.get("union_missing_cell_count") == 0
        and coverage.get("cells_output") is not None
    )
    gates = {
        "no_unexpected_native_failures": not unexpected_failures,
        "only_declared_whole_picture_gates_superseded": (
            set(map(tuple, observed_superseded)) == SUPERSEDED_GATES
        ),
        "paired_mean_relative_tail_pass": paired["all_gates_pass"] is True,
        "master_companion_delivery_pass": delivery["pass"] is True,
        "adaptive_inverse_precision_pass": precision_pass,
        "production_cache_coverage_pass": coverage_pass,
    }
    report = {
        "audit": "V46 final release decision",
        "release": "V46 certified spectral inverse",
        "native_audit": str(args.root / "v46_release_audit.json"),
        "paired_tail_audit": str(
            args.root / "v46_mean_relative_release_audit.json"
        ),
        "delivery_audit": str(args.root / "v46_delivery_audit.json"),
        "precision_audit": str(args.precision),
        "coverage_audit": str(args.coverage),
        "superseded_whole_picture_gates": observed_superseded,
        "supersession_reason": (
            "V77 proved these complete-picture statistics include deterministic "
            "scene colour/detail. V46 replaces only those assertions with an "
            "exact same-path formed-minus-deterministic-mean stochastic audit."
        ),
        "unexpected_native_failures": unexpected_failures,
        "gates": gates,
        "pass": all(gates.values()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
