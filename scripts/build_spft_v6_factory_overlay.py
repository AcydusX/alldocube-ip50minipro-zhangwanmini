#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

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
# factory package. Do not copy it into a distribution build.
TOP_LEVEL_SKIP = {"super.unsparse.img"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mtk_add_checksum(path: Path) -> int:
    """MediaTek ADD checksum: unsigned 32-bit byte sum, odd size padded with FF."""
    total = 0
    size = 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            total = (total + sum(chunk)) & 0xFFFFFFFF
            size += len(chunk)
    if size & 1:
        total = (total + 0xFF) & 0xFFFFFFFF
    return total


def checksum_entries(tree: ET.ElementTree):
    root = tree.getroot()
    images = root.find("images")
    if images is None:
        raise RuntimeError("scatter_checksum.xml has no <images> node")
    entries = images.findall("file")
    if not entries:
        raise RuntimeError("scatter_checksum.xml contains no <file> entries")
    return entries


def validate_stock_checksums(stock: Path, checksum_src: Path) -> ET.ElementTree:
    tree = ET.parse(checksum_src)
    entries = checksum_entries(tree)
    mismatches = []
    checked = 0

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
        actual = mtk_add_checksum(path)
        checked += 1
        if actual != expected:
            mismatches.append((name, expected, actual))

    if mismatches:
        lines = ["Stock MediaTek ADD validation FAILED:"]
        for name, expected, actual in mismatches:
            lines.append(f"  {name}: expected=0x{expected:x} actual=0x{actual:x}")
        raise RuntimeError("\n".join(lines))

    print(f"Validated MediaTek ADD algorithm against {checked} stock checksum entries: PASS")
    return tree


def regenerate_checksum_xml(tree: ET.ElementTree, out: Path) -> None:
    entries = checksum_entries(tree)
    for entry in entries:
        name = entry.get("name")
        assert name is not None
        path = out / name
        if not path.is_file():
            raise FileNotFoundError(f"Output checksum references missing file: {path}")
        value = mtk_add_checksum(path)
        entry.set("chk_method", "ADD")
        entry.set("checksum", f"0x{value:x}")

    # Match the simple stock formatting closely enough for SPFT v6.
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
            "overlay the eight verified custom images, validate the MediaTek "
            "ADD algorithm against the original checksum file, and regenerate "
            "scatter_checksum.xml for the final package."
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
    ]
    for p in required_stock:
        if not p.is_file():
            raise FileNotFoundError(p)

    for src_name in CUSTOM_OVERLAY:
        p = project / src_name
        if not p.is_file():
            raise FileNotFoundError(f"Missing custom overlay image: {p}")

    # Prove the checksum implementation against the untouched factory package
    # before trusting it to generate custom checksum values.
    checksum_tree = validate_stock_checksums(stock, stock / "scatter_checksum.xml")

    copy_factory_tree(stock, out)

    print("Overlaying verified custom images onto factory filenames:")
    for src_name, dst_name in CUSTOM_OVERLAY.items():
        src = project / src_name
        dst = out / dst_name
        shutil.copy2(src, dst)
        print(f"  {src_name} -> {dst_name}")

    # Recalculate all entries, including untouched stock images. This preserves
    # the exact factory checksum list/order while updating the custom payloads.
    regenerate_checksum_xml(checksum_tree, out)

    note = """Alldocube iPlay 50 mini Pro SP Flash Tool v6 factory-overlay package

This package preserves the original factory Download-XML/scatter presentation
and original stock image set, then replaces only these files with the verified
custom Android 16/KPOC/custom-AVB payloads:
  vbmeta.img
  vbmeta_system.img
  vbmeta_vendor.img
  lk.img
  boot.img
  vendor_boot.img
  dtbo.img
  super.img

scatter_checksum.xml was regenerated after first validating the MediaTek ADD
checksum algorithm against every entry in the untouched original stock package.

Load:
  download_agent/flash.xml

IMPORTANT:
The factory XML has the same default download selections as the original
firmware. That includes preloader and userdata when the stock XML enables them.
Flashing userdata erases user data. Flashing preloader is unnecessary for a
normal custom-system reinstall and carries more recovery risk than leaving it
untouched. Uncheck any partition you do not intend to rewrite before Download.
"""
    (out / "CUSTOM-OVERLAY-NOTES.txt").write_text(note, encoding="utf-8")

    manifest = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            manifest.append(f"{sha256_file(p)}  {p.relative_to(out).as_posix()}")
    (out / "SHA256SUMS.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")

    print("Created factory-style package:", out)
    print("Download-XML:", out / "download_agent" / "flash.xml")
    print("Regenerated:", out / "scatter_checksum.xml")
    print("Factory scatter/download selections preserved unchanged.")


if __name__ == "__main__":
    main()
