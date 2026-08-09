#!/usr/bin/env python3
"""Fail a V36 release when native masters or web media use the wrong window."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = {
    "T002": {"start_frame": 0, "frames": 24},
    "T007": {"start_frame": 276, "frames": 24},
    "T031": {"start_frame": 132, "frames": 24},
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("native_root", type=Path)
    parser.add_argument("web_manifest", type=Path)
    args = parser.parse_args()
    checks: list[dict[str, object]] = []

    for scene, expected in EXPECTED.items():
        for branch in ("projection", "bluray_scan"):
            manifest_path = args.native_root / scene / branch / "manifest.json"
            if scene == "T002" and not manifest_path.exists():
                # V36 has no image change and explicitly reuses the already
                # correct V35 T002 control; the web manifest records that path.
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            observed = {
                "start_frame": int(manifest["start_frame"]),
                "frames": int(manifest["frames_processed"]),
            }
            if observed != expected:
                raise RuntimeError(
                    f"{scene}/{branch}: {observed}; expected {expected}"
                )
            checks.append({"path": str(manifest_path), **observed, "pass": True})

    web = json.loads(args.web_manifest.read_text(encoding="utf-8"))
    web_windows = web["absolute_source_frame_contract"]
    for scene, expected in EXPECTED.items():
        key = scene.lower()
        wanted = [expected["start_frame"], expected["start_frame"] + 23]
        observed = list(web_windows[key])
        if observed != wanted:
            raise RuntimeError(f"web {scene}: {observed}; expected {wanted}")
        checks.append({"web_scene": scene, "window": observed, "pass": True})

    print(json.dumps({"contract": EXPECTED, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
