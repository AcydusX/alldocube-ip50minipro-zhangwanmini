#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

TARGET_STORAGE_NAME = "UFS"
TARGET_STORAGE_VALUE = "HW_STORAGE_UFS"

IMAGE_MAP = {
    "vbmeta_a": ("vbmeta_a.img", "vbmeta.img"),
    "vbmeta_system_a": ("vbmeta_system_a.img", "vbmeta_system.img"),
    "vbmeta_vendor_a": ("vbmeta_vendor_a.img", "vbmeta_vendor.img"),
    "lk_a": ("lk_a.img", "lk.img"),
    "boot_a": ("boot_a.img", "boot.img"),
    "vendor_boot_a": ("vendor_boot_a.img", "vendor_boot.img"),
    "dtbo_a": ("dtbo_a.img", "dtbo.img"),
    "super": ("super.img", "super.img"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text(node: ET.Element, name: str) -> str:
    child = node.find(name)
    return (child.text or "").strip() if child is not None else ""


def set_text(node: ET.Element, name: str, value: str) -> None:
    child = node.find(name)
    if child is None:
        raise RuntimeError(f"Missing <{name}> in partition {text(node, 'partition_name')}")
    child.text = value


def copy_tree_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        shutil.copytree(src, dst)


def indent_xml(elem: ET.Element, level: int = 0) -> None:
    # Python's ElementTree.indent() is available on modern Python, but keep this
    # repository helper compatible with older Python 3 installations too.
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent_xml(child, level + 1)
        if not elem[-1].tail or not elem[-1].tail.strip():
            elem[-1].tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build a stock-style Alldocube SP Flash Tool v6 Download-XML package."
    )
    ap.add_argument("--stock-dir", required=True, type=Path,
                    help="Original Alldocube stock firmware directory")
    ap.add_argument("--project-dir", required=True, type=Path,
                    help="Verified project package containing *_a.img and super.img")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--storage", choices=["UFS"], default="UFS")
    args = ap.parse_args()

    stock = args.stock_dir.resolve()
    project = args.project_dir.resolve()
    out = args.out.resolve()

    if out.exists():
        raise FileExistsError(f"Output already exists: {out}")

    scatter_src = stock / "MT6789_Android_scatter.xml"
    flash_src = stock / "download_agent" / "flash.xml"
    da_src = stock / "download_agent" / "DA_BR.bin"
    xsd_src = stock / "download_agent" / "flash.xsd"

    for p in (scatter_src, flash_src, da_src, xsd_src):
        if not p.is_file():
            raise FileNotFoundError(p)

    for part, (src_name, _) in IMAGE_MAP.items():
        src = project / src_name
        if not src.is_file():
            raise FileNotFoundError(f"{part}: missing {src}")

    out.mkdir(parents=True)
    (out / "download_agent").mkdir()

    # Preserve the stock Download-XML entry point and exact DA/XSD.
    shutil.copy2(flash_src, out / "download_agent" / "flash.xml")
    shutil.copy2(da_src, out / "download_agent" / "DA_BR.bin")
    shutil.copy2(xsd_src, out / "download_agent" / "flash.xsd")

    # DB is not part of the selected partition writes, but copying it retains
    # the official package shape and diagnostic database files.
    copy_tree_if_exists(stock / "DB", out / "DB")

    tree = ET.parse(scatter_src)
    root = tree.getroot()

    enabled = set()
    seen_target = set()

    for storage_node in root.findall("storage_type"):
        storage_name = storage_node.get("name", "")
        for part_node in storage_node.findall("partition_index"):
            part_name = text(part_node, "partition_name")
            storage_value = text(part_node, "storage")

            # Default-safe behavior: nothing is downloadable unless it is one
            # of our eight selected UFS partitions.
            if part_node.find("file_name") is not None:
                set_text(part_node, "file_name", "NONE")
            if part_node.find("is_download") is not None:
                set_text(part_node, "is_download", "false")

            if (
                storage_name == TARGET_STORAGE_NAME
                and storage_value == TARGET_STORAGE_VALUE
                and part_name in IMAGE_MAP
            ):
                _, dst_name = IMAGE_MAP[part_name]
                set_text(part_node, "file_name", dst_name)
                set_text(part_node, "is_download", "true")
                enabled.add(part_name)
                seen_target.add(part_name)

    missing = sorted(set(IMAGE_MAP) - seen_target)
    if missing:
        raise RuntimeError("UFS XML scatter missing required partitions: " + ", ".join(missing))

    if enabled != set(IMAGE_MAP):
        raise RuntimeError("Unexpected enabled set: " + ", ".join(sorted(enabled)))

    # Keep XML simple and deterministic while retaining the stock schema.
    indent_xml(root)
    scatter_out = out / "MT6789_Android_scatter.xml"
    tree.write(scatter_out, encoding="utf-8", xml_declaration=True)

    # Copy selected payloads to the same generic filenames used by stock.
    for part, (src_name, dst_name) in IMAGE_MAP.items():
        shutil.copy2(project / src_name, out / dst_name)

    # Never copy stock scatter_checksum.xml: it contains checksums for the
    # original stock images and would be stale for our modified package.
    checksum_note = """scatter_checksum.xml intentionally NOT copied.

The stock checksum file contains ADD checksums for the original stock images.
Using it with this custom package would be incorrect.

For a fully stock-style distribution, regenerate scatter_checksum.xml AFTER
this directory is final using a MediaTek CheckSum Generate v6 tool compatible
with XML scatter packages. Do not reuse the original stock checksum values.

The package can be inspected in SP Flash Tool v6 by selecting:
  download_agent/flash.xml

Use Download Only. The XML enables only:
  vbmeta_a
  vbmeta_system_a
  vbmeta_vendor_a
  lk_a
  boot_a
  vendor_boot_a
  dtbo_a
  super

All eMMC entries and all other UFS partitions, including preloader and
userdata, are disabled and use file_name=NONE.
"""
    (out / "REGENERATE-SCATTER-CHECKSUM.txt").write_text(checksum_note, encoding="utf-8")

    notes = """Alldocube iPlay 50 mini Pro custom Android 16/KPOC/AVB package
SP Flash Tool v6 stock-style Download-XML layout

Load in SP Flash Tool v6:
  download_agent/flash.xml

Mode:
  Download Only

Target physical storage:
  UFS

Enabled partitions:
  vbmeta_a
  vbmeta_system_a
  vbmeta_vendor_a
  lk_a
  boot_a
  vendor_boot_a
  dtbo_a
  super

Explicitly not flashed:
  preloader / preloader_backup
  userdata
  metadata
  nvram / nvdata / nvcfg
  persist
  protect1 / protect2
  proinfo
  otp
  frp
  all B-slot physical partitions
  all eMMC scatter entries

Before distribution, regenerate scatter_checksum.xml for these final files
using a MediaTek CheckSum Generate v6 utility. Never reuse the stock checksum.
"""
    (out / "FLASHING-NOTES.txt").write_text(notes, encoding="utf-8")

    # Independent SHA-256 manifest for our own reproducibility.
    manifest_paths = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            manifest_paths.append(p)
    lines = [f"{sha256_file(p)}  {p.relative_to(out).as_posix()}" for p in manifest_paths]
    (out / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Created stock-style SP Flash Tool v6 package:", out)
    print("Download-XML:", out / "download_agent" / "flash.xml")
    print("Scatter XML:", scatter_out)
    print("Enabled UFS partitions:", ", ".join(sorted(enabled)))
    print("IMPORTANT: regenerate scatter_checksum.xml before calling the package final.")


if __name__ == "__main__":
    main()
