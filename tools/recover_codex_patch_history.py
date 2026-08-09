#!/usr/bin/env python3
"""Reconstruct the lost emulsion engine from Codex patch audit records.

The Codex rollout journal stores every successful apply_patch result, including
full contents for additions and unified diffs for updates.  This tool replays
those immutable audit events into a clean destination.  Website files are
excluded because their authoritative copies already live in this repository.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class FileOperation:
    kind: Literal["add", "update", "delete"]
    path: str
    payload: str = ""


@dataclass(frozen=True)
class PatchEvent:
    timestamp: datetime
    call_id: str
    operations: tuple[FileOperation, ...]


def extract_patch_literals(source: str) -> list[str]:
    """Decode JavaScript string literals whose value is an apply_patch payload."""
    decoder = json.JSONDecoder()
    patches: list[str] = []
    cursor = 0
    marker = '"*** Begin Patch'
    while True:
        position = source.find(marker, cursor)
        if position < 0:
            break
        try:
            value, consumed = decoder.raw_decode(source[position:])
        except json.JSONDecodeError:
            cursor = position + len(marker)
            continue
        if isinstance(value, str) and value.startswith("*** Begin Patch"):
            patches.append(value)
        cursor = position + consumed
    return patches


def parse_patch(patch: str) -> tuple[FileOperation, ...]:
    """Parse the small apply_patch envelope without losing repeated file edits."""
    lines = patch.splitlines()
    if not lines or lines[0] != "*** Begin Patch":
        raise ValueError("Missing patch envelope")
    operations: list[FileOperation] = []
    index = 1
    while index < len(lines):
        header = lines[index]
        if header == "*** End Patch":
            break
        prefixes = {
            "*** Add File: ": "add",
            "*** Update File: ": "update",
            "*** Delete File: ": "delete",
        }
        match = next(
            ((prefix, kind) for prefix, kind in prefixes.items() if header.startswith(prefix)),
            None,
        )
        if match is None:
            raise ValueError(f"Unexpected patch header {header!r}")
        prefix, kind = match
        path = header[len(prefix) :]
        index += 1
        body: list[str] = []
        while index < len(lines) and not lines[index].startswith("*** "):
            body.append(lines[index])
            index += 1
        if kind == "add":
            if any(not line.startswith("+") for line in body):
                raise ValueError(f"Malformed add body for {path}")
            payload = "\n".join(line[1:] for line in body) + "\n"
        elif kind == "update":
            payload = "\n".join(body) + "\n"
        else:
            payload = ""
        operations.append(FileOperation(kind=kind, path=path, payload=payload))
    return tuple(operations)


def collect_events(journal_root: Path) -> list[PatchEvent]:
    """Pair successful patch calls with their full, pre-aggregation payloads."""
    events: list[PatchEvent] = []
    seen: set[str] = set()
    for journal in sorted(journal_root.rglob("*.jsonl")):
        pending: dict[str, list[tuple[datetime, str, tuple[FileOperation, ...]]]] = {}
        with journal.open(encoding="utf-8", errors="replace") as stream:
            for raw in stream:
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                payload = record.get("payload", {})
                turn_id = str(
                    payload.get("turn_id")
                    or payload.get("internal_chat_message_metadata_passthrough", {}).get(
                        "turn_id", ""
                    )
                )
                if record.get("type") == "response_item" and payload.get("type") == "custom_tool_call":
                    patches = extract_patch_literals(str(payload.get("input", "")))
                    if patches and turn_id:
                        operations = tuple(
                            operation
                            for patch in patches
                            for operation in parse_patch(patch)
                        )
                        timestamp = datetime.fromisoformat(
                            record["timestamp"].replace("Z", "+00:00")
                        )
                        pending.setdefault(turn_id, []).append(
                            (timestamp, str(payload.get("call_id", "")), operations)
                        )
                    continue
                if (
                    record.get("type") != "event_msg"
                    or payload.get("type") != "patch_apply_end"
                    or not payload.get("success")
                    or not turn_id
                    or not pending.get(turn_id)
                ):
                    continue
                # A failed patch attempt has no patch_apply_end event and may
                # remain pending in the same turn. The successful event belongs
                # to the immediately preceding patch call, so pair from the end.
                _, outer_call_id, operations = pending[turn_id].pop()
                if not outer_call_id or outer_call_id in seen:
                    continue
                seen.add(outer_call_id)
                events.append(
                    PatchEvent(
                        timestamp=datetime.fromisoformat(
                            record["timestamp"].replace("Z", "+00:00")
                        ),
                        call_id=outer_call_id,
                        operations=operations,
                    )
                )
    return sorted(events, key=lambda event: (event.timestamp, event.call_id))


def render_patch(operations: list[tuple[FileOperation, Path]]) -> str:
    lines = ["*** Begin Patch"]
    for operation, target in operations:
        if operation.kind == "add":
            lines.append(f"*** Add File: {target}")
            lines.extend(f"+{line}" for line in operation.payload.splitlines())
        elif operation.kind == "update":
            lines.append(f"*** Update File: {target}")
            lines.extend(operation.payload.splitlines())
        elif operation.kind == "delete":
            lines.append(f"*** Delete File: {target}")
    lines.append("*** End Patch")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("journal_root", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument(
        "--lost-root",
        default=(
            "/Users/tianxing/.codex/.chatgpt-projects/"
            "g-p-6a62e1cf2144819190c9fd2993c3799b/"
            "experiments/emulsion_reconstruction/"
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    destination = args.destination.resolve()
    recovered: set[Path] = set()
    skipped_generated: set[Path] = set()
    operation_count = 0
    patch_executable = shutil.which("apply_patch")
    if not args.dry_run and not patch_executable:
        raise RuntimeError("Codex apply_patch executable is unavailable")
    for event in collect_events(args.journal_root):
        selected: list[tuple[FileOperation, Path]] = []
        created_in_event: set[Path] = set()
        for change in event.operations:
            absolute = change.path
            if not absolute.startswith(args.lost_root):
                continue
            relative = Path(absolute[len(args.lost_root) :])
            # The Git repository already contains the authoritative website.
            # Render outputs were generated rather than authored and may have
            # been patched after creation, so they are deliberately not replayed.
            if not relative.parts or relative.parts[0] in {"site", "outputs"}:
                continue
            # Hourly research tasks updated this generated index concurrently.
            # Recover the individual notes and rebuild the index deterministically.
            if relative == Path("research_notes/INDEX.md"):
                skipped_generated.add(relative)
                continue
            target = destination / relative
            operation = change.kind
            operation_count += 1
            if (
                operation == "update"
                and not target.exists()
                and target not in created_in_event
                and target.suffix.lower() in {".json", ".csv", ".npy", ".npz"}
            ):
                skipped_generated.add(relative)
                continue
            selected.append((change, target))
            if operation == "add":
                created_in_event.add(target)

        if not selected:
            continue
        if not args.dry_run:
            for _, target in selected:
                target.parent.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [patch_executable],
                input=render_patch(selected),
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"{event.timestamp.isoformat()} {event.call_id}: "
                    f"patch replay failed\n{result.stdout}\n{result.stderr}"
                )
        for change, target in selected:
            relative = target.relative_to(destination)
            if change.kind == "delete":
                recovered.discard(relative)
            else:
                recovered.add(relative)

    print(
        json.dumps(
            {
                "events": operation_count,
                "recovered_files": len(recovered),
                "skipped_generated_files": [
                    str(path) for path in sorted(skipped_generated)
                ],
                "destination": str(destination),
                "dry_run": args.dry_run,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
