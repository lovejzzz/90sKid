#!/usr/bin/env python3
"""Find simple ARM64 ADRP+ADD references in a thin Mach-O image.

This intentionally implements only the instruction pair used for position-
independent references to nearby static data. It is a read-only research aid,
not a general disassembler.
"""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def sign_extend(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)


def decode_adrp(word: int, pc: int) -> tuple[int, int] | None:
    if word & 0x9F000000 != 0x90000000:
        return None
    rd = word & 0x1F
    immlo = (word >> 29) & 0x3
    immhi = (word >> 5) & 0x7FFFF
    delta = sign_extend((immhi << 2) | immlo, 21) << 12
    return rd, (pc & ~0xFFF) + delta


def decode_add_imm(word: int) -> tuple[int, int, int] | None:
    if word & 0xFF000000 != 0x91000000:
        return None
    rd = word & 0x1F
    rn = (word >> 5) & 0x1F
    shift = 12 if ((word >> 22) & 1) else 0
    imm = ((word >> 10) & 0xFFF) << shift
    return rd, rn, imm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("targets", nargs="+", type=lambda value: int(value, 0))
    parser.add_argument("--lookahead", type=int, default=8)
    args = parser.parse_args()

    blob = args.binary.read_bytes()
    wanted = set(args.targets)
    for offset in range(0, len(blob) - 4, 4):
        first = struct.unpack_from("<I", blob, offset)[0]
        decoded = decode_adrp(first, offset)
        if decoded is None:
            continue
        reg, page = decoded
        for step in range(1, args.lookahead + 1):
            pos = offset + step * 4
            if pos + 4 > len(blob):
                break
            add = decode_add_imm(struct.unpack_from("<I", blob, pos)[0])
            if add is None:
                continue
            _rd, rn, immediate = add
            if rn != reg:
                continue
            target = page + immediate
            if target in wanted:
                print(
                    f"target=0x{target:x} adrp=0x{offset:x} add=0x{pos:x} "
                    f"register=x{reg} distance={step}"
                )


if __name__ == "__main__":
    main()
