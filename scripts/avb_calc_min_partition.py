#!/usr/bin/env python3
"""Find the minimum 4-KiB-aligned AVB partition size for an image.

Requires avbtool. FEC options are intentionally configurable; the final project
used no-FEC payloads after partition resize, but the sizing investigation also
used stock-style FEC planning.
"""
import argparse
import os
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('image_size', type=int)
p.add_argument('--avbtool', default=str(Path.home() / 'avbtool.py'))
p.add_argument('--fec-roots', type=int, default=None)
a = p.parse_args()

env = os.environ.copy()

def max_image(partition_size):
    cmd = ['python3', a.avbtool, 'add_hashtree_footer', '--partition_size', str(partition_size), '--hash_algorithm', 'sha256', '--calc_max_image_size']
    if a.fec_roots is None:
        cmd.append('--do_not_generate_fec')
    else:
        cmd += ['--fec_num_roots', str(a.fec_roots)]
    return int(subprocess.check_output(cmd, env=env, text=True).strip())

lo = ((a.image_size + 4095) // 4096) * 4096
hi = lo + 256 * 1024 * 1024
while lo < hi:
    mid = (((lo + hi) // 2) // 4096) * 4096
    if mid < lo:
        mid = lo
    if max_image(mid) >= a.image_size:
        hi = mid
    else:
        lo = mid + 4096

print(f'image_size={a.image_size}')
print(f'min_partition_size={lo}')
print(f'min_partition_hex=0x{lo:X}')
print(f'max_payload_at_min={max_image(lo)}')
print(f'extra_bytes={lo-a.image_size}')
