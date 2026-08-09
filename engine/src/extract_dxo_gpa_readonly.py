#!/usr/bin/env python3
"""Read-only extractor and inventory tool for DxO's DGPA resource archives.

The source archive is never opened for writing. Extracted payloads and a JSON
manifest are written to a caller-selected research directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HEADER_SIZE = 10
ENTRY_SIZE = 16


def png_ihdr(payload: bytes) -> dict[str, int] | None:
    if not payload.startswith(PNG_SIGNATURE) or len(payload) < 33:
        return None
    chunk_length = struct.unpack_from(">I", payload, 8)[0]
    if payload[12:16] != b"IHDR" or chunk_length != 13:
        return None
    width, height, bit_depth, color_type, compression, filtering, interlace = (
        struct.unpack_from(">IIBBBBB", payload, 16)
    )
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "compression": compression,
        "filtering": filtering,
        "interlace": interlace,
    }


def parse_archive(source: Path) -> tuple[dict[str, int], list[dict[str, object]], bytes]:
    blob = source.read_bytes()
    if len(blob) < HEADER_SIZE or blob[:4] != b"DGPA":
        raise ValueError(f"Not a DGPA archive: {source}")

    major, minor, count = struct.unpack_from("<BBI", blob, 4)
    table_end = HEADER_SIZE + count * ENTRY_SIZE
    if table_end > len(blob):
        raise ValueError("DGPA index extends beyond the source archive")

    entries: list[dict[str, object]] = []
    for index in range(count):
        pos = HEADER_SIZE + index * ENTRY_SIZE
        resource_id, resource_type, offset, size = struct.unpack_from("<IIII", blob, pos)
        end = offset + size
        if offset < table_end or end > len(blob) or end < offset:
            raise ValueError(
                f"Invalid payload extent for entry {index}: offset={offset}, size={size}"
            )
        payload = blob[offset:end]
        entries.append(
            {
                "index": index,
                "resource_id": resource_id,
                "resource_type": resource_type,
                "offset": offset,
                "size": size,
                "end": end,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "format": "png" if payload.startswith(PNG_SIGNATURE) else "unknown",
                "png_ihdr": png_ihdr(payload),
            }
        )

    return {"major": major, "minor": minor, "count": count, "table_end": table_end}, entries, blob


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    header, entries, blob = parse_archive(source)
    output.mkdir(parents=True, exist_ok=True)

    previous_end = header["table_end"]
    all_contiguous = True
    for entry in entries:
        offset = int(entry["offset"])
        end = int(entry["end"])
        if offset != previous_end:
            all_contiguous = False
        previous_end = end
        suffix = ".png" if entry["format"] == "png" else ".bin"
        filename = (
            f"{int(entry['index']):03d}_id{int(entry['resource_id']):04d}"
            f"_type{int(entry['resource_type']):02d}{suffix}"
        )
        (output / filename).write_bytes(blob[offset:end])
        entry["filename"] = filename

    manifest = {
        "source": str(source),
        "source_size": len(blob),
        "source_sha256": hashlib.sha256(blob).hexdigest(),
        "archive": header,
        "all_payloads_contiguous": all_contiguous,
        "last_payload_ends_at_eof": bool(entries and entries[-1]["end"] == len(blob)),
        "entries": entries,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "source": str(source),
                "count": len(entries),
                "png_count": sum(entry["format"] == "png" for entry in entries),
                "all_payloads_contiguous": all_contiguous,
                "last_payload_ends_at_eof": manifest["last_payload_ends_at_eof"],
                "output": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
