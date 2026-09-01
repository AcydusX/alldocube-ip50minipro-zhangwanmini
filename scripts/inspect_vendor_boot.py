#!/usr/bin/env python3
"""Inspect Android vendor_boot v4 structural size without modifying the image."""
import struct
import sys
from pathlib import Path


def u32(b, off):
    return struct.unpack_from('<I', b, off)[0]


def align(v, a):
    return (v + a - 1) // a * a


def inspect(fn):
    p = Path(fn)
    with p.open('rb') as f:
        h = f.read(4096)
    if h[:8] != b'VNDRBOOT':
        raise SystemExit(f'{p}: not a vendor_boot image')
    version = u32(h, 8)
    page = u32(h, 12)
    ramdisk = u32(h, 24)
    header_size = u32(h, 2096)
    dtb = u32(h, 2100)
    table = entries = entry_size = bootconfig = 0
    if version >= 4:
        table = u32(h, 2112)
        entries = u32(h, 2116)
        entry_size = u32(h, 2120)
        bootconfig = u32(h, 2124)
    structural = align(header_size, page) + align(ramdisk, page) + align(dtb, page)
    if version >= 4:
        structural += align(table, page) + align(bootconfig, page)
    with p.open('rb') as f:
        f.seek(structural)
        tail = f.read()
    print(f'file={p}')
    print(f'version={version}')
    print(f'page_size={page}')
    print(f'header_size={header_size}')
    print(f'vendor_ramdisk_size={ramdisk}')
    print(f'dtb_size={dtb}')
    print(f'ramdisk_table_size={table}')
    print(f'table_entries={entries}')
    print(f'table_entry_size={entry_size}')
    print(f'bootconfig_size={bootconfig}')
    print(f'structural_used_size={structural}')
    print(f'structural_used_hex=0x{structural:X}')
    print(f'physical_file_size={p.stat().st_size}')
    print(f'tail_all_zero={not any(tail)}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(f'usage: {sys.argv[0]} vendor_boot.img [...]')
    for arg in sys.argv[1:]:
        inspect(arg)
        print()
