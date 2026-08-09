#!/usr/bin/env python3
"""Create or verify the versioned engine-source recovery manifest."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess


REPOSITORY = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("SOURCE_MANIFEST.sha256")


def protected_paths() -> list[Path]:
    payload = subprocess.check_output(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "engine",
        ],
        cwd=REPOSITORY,
        text=True,
    )
    paths: list[Path] = []
    for name in payload.splitlines():
        path = Path(name)
        if path == MANIFEST.relative_to(REPOSITORY):
            continue
        # ``git ls-files`` still reports a tracked path deleted in the current
        # worktree. The manifest already catches that case on normal verify;
        # --write inventories the files that actually exist in the candidate.
        if not (REPOSITORY / path).is_file():
            continue
        if any(part in {"cache", "outputs", "work", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".swift", ".metal", ".md", ".json", ".npz"}:
            continue
        paths.append(path)
    return sorted(set(paths))


def digest(path: Path) -> str:
    return hashlib.sha256((REPOSITORY / path).read_bytes()).hexdigest()


def build_manifest() -> str:
    return "".join(f"{digest(path)}  {path.as_posix()}\n" for path in protected_paths())


def verify() -> None:
    expected: dict[Path, str] = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        checksum, name = line.split("  ", 1)
        expected[Path(name)] = checksum
    current = set(protected_paths())
    recorded = set(expected)
    if current != recorded:
        missing = sorted(str(path) for path in recorded - current)
        unrecorded = sorted(str(path) for path in current - recorded)
        raise SystemExit(
            f"engine source inventory drift; missing={missing}, unrecorded={unrecorded}"
        )
    changed = [str(path) for path, checksum in expected.items() if digest(path) != checksum]
    if changed:
        raise SystemExit(f"engine source checksum drift: {changed}")
    print(f"engine source integrity verified: {len(expected)} protected files")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        MANIFEST.write_text(build_manifest(), encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(REPOSITORY)}")
    else:
        verify()


if __name__ == "__main__":
    main()
