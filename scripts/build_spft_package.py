#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, re, shutil, struct
from pathlib import Path

SELECTED = {
    "lk_a": ("lk-custom-avb.img", "lk_a.img"),
    "boot_a": ("boot_a.img", "boot_a.img"),
    "dtbo_a": ("dtbo_a.img", "dtbo_a.img"),
    "vendor_boot_a": ("vendor_boot_a.img", "vendor_boot_a.img"),
    "vbmeta_a": ("vbmeta_a.img", "vbmeta_a.img"),
    "vbmeta_system_a": ("vbmeta_system_a.img", "vbmeta_system_a.img"),
    "vbmeta_vendor_a": ("vbmeta_vendor_a.img", "vbmeta_vendor_a.img"),
    "super": (None, "super.img"),
}
SPARSE_MAGIC = 0xED26FF3A
STORAGE_MAP = {
    "EMMC": "HW_STORAGE_EMMC",
    "UFS": "HW_STORAGE_UFS",
}


def parse_num(v: str) -> int:
    return int(v.strip(), 0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def expanded_image_size(path: Path):
    with path.open("rb") as f:
        hdr = f.read(28)
    if len(hdr) >= 28 and struct.unpack_from("<I", hdr, 0)[0] == SPARSE_MAGIC:
        major, minor, file_hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, checksum = struct.unpack_from("<HHHHIIII", hdr, 4)
        if major != 1:
            raise RuntimeError(f"Unsupported sparse image version {major}: {path}")
        return blk_sz * total_blks, "android-sparse"
    return path.stat().st_size, "raw"


def find_scatter(stock_dir: Path) -> Path:
    cands = sorted(stock_dir.glob("*scatter*.txt"))
    if not cands:
        cands = sorted(stock_dir.rglob("*scatter*.txt"))
    if not cands:
        raise FileNotFoundError("No *scatter*.txt found under stock firmware directory")
    if len(cands) > 1:
        print("Scatter candidates:")
        for c in cands:
            print(" ", c)
        print("Using:", cands[0])
    else:
        print("Using scatter:", cands[0])
    return cands[0]


def split_scatter(text: str):
    text = text.lstrip("\ufeff")
    block_re = re.compile(r"(?m)^[ \t]*-[ \t]*partition_index[ \t]*:[ \t]*")
    matches = list(block_re.finditer(text))
    if not matches:
        preview = "\n".join(text.splitlines()[:40])
        raise RuntimeError(
            "Scatter partition blocks not recognized. "
            "The selected file may use a different SP Flash Tool v6 format.\n"
            "Selected scatter preview:\n" + preview
        )
    prefix = text[:matches[0].start()]
    blocks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append(text[start:end])
    return prefix, blocks


def field(block: str, name: str):
    m = re.search(rf"(?m)^\s*{re.escape(name)}:\s*(.*?)\s*$", block)
    return m.group(1) if m else None


def set_field(block: str, name: str, value: str) -> str:
    pat = rf"(?m)^(\s*{re.escape(name)}:\s*).*?$"
    if not re.search(pat, block):
        raise RuntimeError(f"Missing field {name!r} in block {field(block,'partition_name')}")
    return re.sub(pat, lambda m: m.group(1) + value, block, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stock-dir", required=True, type=Path)
    ap.add_argument("--deploy-dir", required=True, type=Path)
    ap.add_argument("--super", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument(
        "--storage",
        choices=sorted(STORAGE_MAP),
        help="Target physical storage layout. Required when the scatter contains both eMMC and UFS layouts.",
    )
    ap.add_argument("--no-hash", action="store_true")
    ap.add_argument("--show-super-region", action="store_true")
    args = ap.parse_args()

    stock = args.stock_dir.resolve()
    deploy = args.deploy_dir.resolve()
    super_img = args.super.resolve()
    out = args.out.resolve()

    scatter = find_scatter(stock)
    raw = scatter.read_text(encoding="utf-8", errors="replace")
    prefix, blocks = split_scatter(raw)

    selected_blocks = [b for b in blocks if field(b, "partition_name") in SELECTED]
    available_storages = sorted({field(b, "storage") for b in selected_blocks if field(b, "storage")})
    print("Scatter storage layouts:", ", ".join(available_storages) or "unknown")

    if args.storage:
        target_storage = STORAGE_MAP[args.storage]
        if target_storage not in available_storages:
            raise RuntimeError(
                f"Requested --storage {args.storage}, but {target_storage} was not found in the selected scatter blocks"
            )
    else:
        if len(available_storages) != 1:
            raise RuntimeError(
                "Scatter contains multiple physical storage layouts. Re-run with exactly one of: "
                "--storage EMMC or --storage UFS.\n"
                "Determine the actual device storage first; do not flash a scatter with both layouts enabled."
            )
        target_storage = available_storages[0]

    print("Target storage:", target_storage)

    scatter_by_name = {}
    for b in blocks:
        name = field(b, "partition_name")
        storage = field(b, "storage")
        if name in SELECTED and storage == target_storage:
            if name in scatter_by_name:
                raise RuntimeError(f"Duplicate {name} block for target storage {target_storage}")
            scatter_by_name[name] = b

    missing = [p for p in SELECTED if p not in scatter_by_name]
    if missing:
        raise RuntimeError(
            f"Target storage {target_storage} lacks required partitions: " + ", ".join(missing)
        )

    sb = scatter_by_name["super"]
    sstart = field(sb, "physical_start_addr") or field(sb, "linear_start_addr")
    ssize = field(sb, "partition_size")
    sregion = field(sb, "region")
    print(f"SUPER region: storage={target_storage} region={sregion} start={sstart} size={ssize} ({parse_num(ssize)} bytes)")
    if args.show_super_region:
        print(f"Use this start/size for a {target_storage} super readback in region {sregion}.")

    sources = {}
    for part, (src_name, out_name) in SELECTED.items():
        src = super_img if part == "super" else deploy / src_name
        if not src.is_file():
            raise FileNotFoundError(f"{part}: missing source file: {src}")
        sources[part] = (src, out_name)

    for part, (src, out_name) in sources.items():
        psize = parse_num(field(scatter_by_name[part], "partition_size"))
        expanded, kind = expanded_image_size(src)
        print(f"{part:18s} {kind:14s} expanded={expanded} partition={psize}")
        if expanded > psize:
            raise RuntimeError(f"{part}: image exceeds scatter partition size")

    if out.exists():
        raise FileExistsError(f"Output directory already exists: {out}")
    out.mkdir(parents=True)

    for part, (src, out_name) in sources.items():
        shutil.copy2(src, out / out_name)

    new_blocks = []
    for b in blocks:
        name = field(b, "partition_name")
        storage = field(b, "storage")
        if name in SELECTED and storage == target_storage:
            b = set_field(b, "file_name", SELECTED[name][1])
            b = set_field(b, "is_download", "true")
        else:
            b = set_field(b, "file_name", "NONE")
            b = set_field(b, "is_download", "false")
        new_blocks.append(b)

    out_scatter = out / scatter.name.replace(".txt", "_PROJECT.txt")
    out_scatter.write_text(prefix + "".join(new_blocks), encoding="utf-8")

    enabled_names = "\n".join(f"  {name}" for name in SELECTED)
    notes = f"""Alldocube iPlay 50 mini Pro - SP Flash Tool project package

Target physical storage:
  {target_storage}

Enabled partitions on that storage layout only:
{enabled_names}

All other scatter entries, including the alternate storage layout, are disabled and file_name=NONE.

IMPORTANT:
- Use SP Flash Tool: Download Only.
- Do NOT use Format All + Download.
- Do NOT enable preloader unless doing deliberate stock recovery.
- userdata, metadata, NVRAM/NVDATA, calibration and identity partitions are not part of this package.
- lk_b is intentionally not overwritten.
- super.img is the physical super image containing the final dynamic layout.
- Keep the full stock firmware separately for recovery.

Project-generation runtime vbmeta digest:
  2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898
"""
    (out / "FLASHING-NOTES.txt").write_text(notes, encoding="utf-8")

    if not args.no_hash:
        lines = []
        for p in sorted(out.iterdir()):
            if p.is_file() and p.name != "SHA256SUMS.txt":
                lines.append(f"{sha256_file(p)}  {p.name}")
        (out / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Created:", out)
    print("Scatter:", out_scatter)
    print("Target storage:", target_storage)
    print("Use: Download Only")


if __name__ == "__main__":
    main()
