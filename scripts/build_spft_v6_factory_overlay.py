#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - host dependency check
    raise SystemExit(
        "This builder requires NumPy for fast checksum generation on multi-GB images.\n"
        "Install it on Ubuntu/WSL with: sudo apt install python3-numpy"
    ) from exc

CUSTOM_OVERLAY = {
    "vbmeta_a.img": "vbmeta.img",
    "vbmeta_system_a.img": "vbmeta_system.img",
    "vbmeta_vendor_a.img": "vbmeta_vendor.img",
    "lk_a.img": "lk.img",
    "boot_a.img": "boot.img",
    "vendor_boot_a.img": "vendor_boot.img",
    "dtbo_a.img": "dtbo.img",
    "super.img": "super.img",
}

# This file was created locally during analysis and is not part of the original
# factory release. Do not copy it into a distribution build.
TOP_LEVEL_SKIP = {"super.unsparse.img"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mtk_v6_add_checksum(path: Path) -> int:
    """Return the MediaTek v6 scatter chk_method=ADD checksum.

    Proven against the original Alldocube iPlay 50 mini Pro factory
    scatter_checksum.xml:
      * sum complete 32-bit LITTLE-ENDIAN words modulo 2^32;
      * if 1-3 bytes remain at EOF, add those trailing bytes individually.

    The trailing-byte rule is required by the stock csci.ini (size % 4 == 2).
    NumPy keeps this practical for multi-gigabyte sparse super images.
    """
    total = 0
    tail = b""
    chunk_size = 64 * 1024 * 1024

    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            if tail:
                chunk = tail + chunk
                tail = b""

            usable = len(chunk) & ~3
            if usable:
                words = np.frombuffer(memoryview(chunk)[:usable], dtype="<u4")
                total = (total + int(words.sum(dtype=np.uint64))) & 0xFFFFFFFF
            tail = chunk[usable:]

    if tail:
        total = (total + sum(tail)) & 0xFFFFFFFF

    return total


def checksum_entries(tree: ET.ElementTree) -> list[ET.Element]:
    images = tree.getroot().find("images")
    if images is None:
        raise RuntimeError("scatter_checksum.xml has no <images> node")
    entries = images.findall("file")
    if not entries:
        raise RuntimeError("scatter_checksum.xml contains no <file> entries")
    return entries


def validate_stock_checksums(stock: Path, checksum_src: Path) -> ET.ElementTree:
    tree = ET.parse(checksum_src)
    entries = checksum_entries(tree)
    mismatches: list[tuple[str, int, int]] = []
    checked = 0

    print("Validating MediaTek v6 ADD algorithm against original factory checksums...")
    for entry in entries:
        name = entry.get("name")
        method = (entry.get("chk_method") or "").upper()
        expected_text = entry.get("checksum")
        if not name or not expected_text:
            raise RuntimeError("Malformed entry in stock scatter_checksum.xml")
        if method != "ADD":
            raise RuntimeError(f"Unsupported checksum method for {name}: {method}")

        path = stock / name
        if not path.is_file():
            raise FileNotFoundError(f"Stock checksum references missing file: {path}")

        expected = int(expected_text, 0)
        actual = mtk_v6_add_checksum(path)
        checked += 1
        status = "PASS" if actual == expected else "FAIL"
        print(f"  {status:4s} {name:32s} expected=0x{expected:08x} actual=0x{actual:08x}")
        if actual != expected:
            mismatches.append((name, expected, actual))

    if mismatches:
        lines = ["Stock MediaTek v6 ADD validation FAILED:"]
        for name, expected, actual in mismatches:
            lines.append(
                f"  {name}: expected=0x{expected:08x} actual=0x{actual:08x}"
            )
        raise RuntimeError("\n".join(lines))

    print(f"Stock checksum validation: PASS ({checked}/{checked} entries)")
    return tree


def regenerate_checksum_xml(tree: ET.ElementTree, out: Path) -> None:
    print("Regenerating scatter_checksum.xml for final factory-overlay payloads...")
    for entry in checksum_entries(tree):
        name = entry.get("name")
        assert name is not None
        path = out / name
        if not path.is_file():
            raise FileNotFoundError(f"Output checksum references missing file: {path}")
        value = mtk_v6_add_checksum(path)
        entry.set("chk_method", "ADD")
        entry.set("checksum", f"0x{value:08x}")
        print(f"  {name:32s} 0x{value:08x}")

    ET.indent(tree, space="        ")
    tree.write(out / "scatter_checksum.xml", encoding="UTF-8", xml_declaration=True)


def copy_factory_tree(stock: Path, out: Path) -> None:
    out.mkdir(parents=True)
    for src in stock.iterdir():
        if src.name in TOP_LEVEL_SKIP:
            continue
        dst = out / src.name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Clone the original Alldocube SP Flash Tool v6 factory package, "
            "overlay the eight verified custom Android/KPOC/AVB images, prove "
            "the MediaTek v6 ADD checksum against the untouched factory package, "
            "and regenerate scatter_checksum.xml."
        )
    )
    ap.add_argument("--stock-dir", required=True, type=Path)
    ap.add_argument("--project-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    stock = args.stock_dir.resolve()
    project = args.project_dir.resolve()
    out = args.out.resolve()

    if out.exists():
        raise FileExistsError(f"Output already exists: {out}")

    required_stock = [
        stock / "MT6789_Android_scatter.xml",
        stock / "scatter_checksum.xml",
        stock / "download_agent" / "flash.xml",
        stock / "download_agent" / "DA_BR.bin",
        stock / "download_agent" / "flash.xsd",
    ]
    for p in required_stock:
        if not p.is_file():
            raise FileNotFoundError(p)

    for src_name in CUSTOM_OVERLAY:
        p = project / src_name
        if not p.is_file():
            raise FileNotFoundError(f"Missing custom overlay image: {p}")

    # Critical safety gate: do not generate a custom checksum file unless our
    # implementation reproduces every checksum in the untouched factory set.
    checksum_tree = validate_stock_checksums(stock, stock / "scatter_checksum.xml")

    copy_factory_tree(stock, out)

    print("Overlaying verified custom images onto factory filenames:")
    for src_name, dst_name in CUSTOM_OVERLAY.items():
        src = project / src_name
        dst = out / dst_name
        shutil.copy2(src, dst)
        print(f"  {src_name:24s} -> {dst_name}")

    # Preserve the exact factory checksum list/order, while recalculating values
    # for both untouched stock images and the eight overlaid custom payloads.
    regenerate_checksum_xml(checksum_tree, out)

    note = """Alldocube iPlay 50 mini Pro SP Flash Tool v6 factory-overlay package

This package preserves the original factory Download-XML, XML scatter, stock
image set, default table presentation, DA and database files. Only these factory
filenames are replaced by the verified custom Android 16/KPOC/custom-AVB stack:
  vbmeta.img
  vbmeta_system.img
  vbmeta_vendor.img
  lk.img
  boot.img
  vendor_boot.img
  dtbo.img
  super.img

scatter_checksum.xml was regenerated with the MediaTek v6 ADD algorithm only
after that algorithm reproduced every checksum in the untouched original
Alldocube factory package.

Load in SP Flash Tool v6:
  download_agent/flash.xml

The factory XML's normal rows/default selections are intentionally preserved.
Review the table before pressing Download. In particular, userdata erases user
data and preloader normally does not need to be rewritten for a custom-system
reinstall.
"""
    (out / "CUSTOM-OVERLAY-NOTES.txt").write_text(note, encoding="utf-8")

    manifest = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            manifest.append(f"{sha256_file(p)}  {p.relative_to(out).as_posix()}")
    (out / "SHA256SUMS.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")

    print()
    print("Created factory-style package:", out)
    print("Download-XML:", out / "download_agent" / "flash.xml")
    print("Regenerated:", out / "scatter_checksum.xml")
    print("Factory XML scatter and default download selections preserved unchanged.")


if __name__ == "__main__":
    main()
