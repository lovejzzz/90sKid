#!/usr/bin/env python3
"""Extract DxO's static rendering-profile registry without modifying the binary.

This is a research reproducibility tool for the locally installed ARM64 slice of
DxOCorrectionEngine.  The table location and record count are version-specific,
so both are explicit command-line parameters and every decoded pointer is
validated before a record is accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


RECORD = struct.Struct("<QIIII")


def read_c_string(blob: bytes, offset: int, max_length: int = 256) -> str:
    if not 0 <= offset < len(blob):
        raise ValueError(f"string pointer outside file: 0x{offset:x}")
    end = blob.find(b"\0", offset, min(len(blob), offset + max_length))
    if end < 0:
        raise ValueError(f"unterminated string at 0x{offset:x}")
    raw = blob[offset:end]
    if not raw or any(byte < 0x20 or byte > 0x7E for byte in raw):
        raise ValueError(f"non-ASCII registry name at 0x{offset:x}")
    return raw.decode("ascii")


def parse_registry(blob: bytes, table_offset: int, count: int) -> list[dict[str, object]]:
    table_end = table_offset + count * RECORD.size
    if table_offset < 0 or table_end > len(blob):
        raise ValueError("registry table extends beyond binary")

    records: list[dict[str, object]] = []
    for index in range(count):
        offset = table_offset + index * RECORD.size
        name_pointer, resource_id, category, black_white, reserved = RECORD.unpack_from(
            blob, offset
        )
        records.append(
            {
                "index": index,
                "record_offset": offset,
                "name_pointer": name_pointer,
                "name": read_c_string(blob, name_pointer),
                "resource_id": resource_id,
                "category": category,
                "black_white": bool(black_white),
                "black_white_raw": black_white,
                "reserved": reserved,
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--archive-manifest", type=Path)
    parser.add_argument("--table-offset", type=lambda value: int(value, 0), default=0x3A1F428)
    parser.add_argument("--count", type=int, default=262)
    args = parser.parse_args()

    binary = args.binary.resolve(strict=True)
    blob = binary.read_bytes()
    records = parse_registry(blob, args.table_offset, args.count)

    archive_by_id: dict[int, dict[str, object]] = {}
    manifest_path: str | None = None
    if args.archive_manifest:
        manifest = json.loads(args.archive_manifest.resolve(strict=True).read_text())
        manifest_path = str(args.archive_manifest.resolve())
        archive_by_id = {
            int(entry["resource_id"]): entry for entry in manifest.get("entries", [])
        }

    for record in records:
        entry = archive_by_id.get(int(record["resource_id"]))
        record["archive_entry"] = (
            {
                "index": entry["index"],
                "filename": entry["filename"],
                "sha256": entry["sha256"],
                "png_ihdr": entry["png_ihdr"],
            }
            if entry
            else None
        )

    black_white_records = [record for record in records if record["black_white"]]
    matched_black_white = [
        record for record in black_white_records if record["archive_entry"] is not None
    ]
    result = {
        "source": str(binary),
        "source_size": len(blob),
        "source_sha256": hashlib.sha256(blob).hexdigest(),
        "table_offset": args.table_offset,
        "record_size": RECORD.size,
        "record_count": len(records),
        "archive_manifest": manifest_path,
        "black_white_count": len(black_white_records),
        "black_white_archive_match_count": len(matched_black_white),
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "records": len(records),
                "black_white": len(black_white_records),
                "black_white_with_archive_patch": len(matched_black_white),
                "output": str(args.output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
