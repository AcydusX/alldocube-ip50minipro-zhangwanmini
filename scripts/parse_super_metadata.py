#!/usr/bin/env python3
"""Read Android LP metadata from a raw/unsparsed super image.

This is a read-only extraction helper based on the format used during the
project. It validates geometry/header/table SHA-256 checksums before listing
partitions and extents.
"""
import argparse
import hashlib
import struct
from pathlib import Path

GEOM_MAGIC = 0x616C4467
HEADER_MAGIC = 0x414C5030
RESERVED = 4096
GEOM_SIZE = 4096
SECTOR = 512

ap = argparse.ArgumentParser()
ap.add_argument('super_raw')
ap.add_argument('--extract-dir')
ap.add_argument('--partitions', nargs='*')
a = ap.parse_args()
p = Path(a.super_raw)

with p.open('rb') as f:
    f.seek(RESERVED)
    g = bytearray(f.read(52))
    magic, struct_size = struct.unpack_from('<II', g, 0)
    checksum = bytes(g[8:40])
    metadata_max_size, slot_count, logical_block_size = struct.unpack_from('<III', g, 40)
    chk = bytearray(g[:struct_size]); chk[8:40] = b'\0'*32
    if magic != GEOM_MAGIC or hashlib.sha256(chk).digest() != checksum:
        raise SystemExit('geometry validation failed')
    metadata_offset = RESERVED + GEOM_SIZE * 2
    f.seek(metadata_offset)
    first = f.read(256)
    hmagic = struct.unpack_from('<I', first, 0)[0]
    major, minor = struct.unpack_from('<HH', first, 4)
    header_size = struct.unpack_from('<I', first, 8)[0]
    header_checksum = first[12:44]
    tables_size = struct.unpack_from('<I', first, 44)[0]
    tables_checksum = first[48:80]
    if hmagic != HEADER_MAGIC:
        raise SystemExit('metadata magic failed')
    header = bytearray(first[:header_size]); header[12:44] = b'\0'*32
    if hashlib.sha256(header).digest() != header_checksum:
        raise SystemExit('header checksum failed')
    def td(off): return struct.unpack_from('<III', first, off)
    poff,pnum,psz = td(80); eoff,enum,esz = td(92)
    f.seek(metadata_offset + header_size)
    tables = f.read(tables_size)
    if hashlib.sha256(tables).digest() != tables_checksum:
        raise SystemExit('tables checksum failed')

parts=[]
for i in range(pnum):
    e=tables[poff+i*psz:poff+(i+1)*psz]
    name=e[:36].split(b'\0',1)[0].decode()
    attrs,first_extent,num_extents,group=struct.unpack_from('<IIII',e,36)
    parts.append((name,attrs,first_extent,num_extents,group))
ext=[]
for i in range(enum):
    e=tables[eoff+i*esz:eoff+(i+1)*esz]
    ext.append(struct.unpack_from('<QIQI',e,0))

print(f'metadata_version={major}.{minor}')
print(f'metadata_max_size={metadata_max_size}')
print(f'slot_count={slot_count}')
print(f'logical_block_size={logical_block_size}')

selected=set(a.partitions or [x[0] for x in parts])
extractions={}
for name,attrs,first_extent,num_extents,group in parts:
    if name not in selected: continue
    total=0; ranges=[]
    print(f'[{name}]')
    for n in range(num_extents):
        sectors,target_type,target_data,target_source=ext[first_extent+n]
        size=sectors*SECTOR; offset=target_data*SECTOR
        total += size; ranges.append((offset,size,target_type))
        print(f'extent={n} offset={offset} size={size} type={target_type} source={target_source}')
    print(f'total={total} hex=0x{total:X}')
    extractions[name]=ranges

if a.extract_dir:
    out=Path(a.extract_dir); out.mkdir(parents=True,exist_ok=True)
    with p.open('rb') as src:
        for name,ranges in extractions.items():
            dst=out/f'{name}.img'
            with dst.open('wb') as o:
                for offset,size,target_type in ranges:
                    if target_type != 0:
                        raise SystemExit(f'{name}: unsupported non-linear extent type {target_type}')
                    src.seek(offset); remaining=size
                    while remaining:
                        data=src.read(min(8*1024*1024,remaining))
                        if not data: raise SystemExit('unexpected EOF')
                        o.write(data); remaining-=len(data)
            print(f'extracted {name} -> {dst} ({dst.stat().st_size})')
