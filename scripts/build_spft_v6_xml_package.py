#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

# The official Alldocube XML scatter carries both EMMC and UFS storage layouts.
# SP Flash Tool v6 may populate its image table from the first layout before the
# DA has connected to a device and identified the actual storage.  Therefore a
# stock-style package must retain the selected image entries in both layouts.
# The DA resolves the real hardware storage at connection time.  On the tested
# tablet the actual super block device is /dev/block/sdc60 (UFS).
STOCK_STORAGE_LAYOUTS = {
    "EMMC": "HW_STORAGE_EMMC",
    "UFS": "HW_STORAGE_UFS",
}

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
    # Kept for command-line compatibility and to document the tested device.
    # The output XML intentionally retains both stock storage branches.
    ap.add_argument("--storage", choices=["UFS"], default="UFS",
                    help="Actual tested device storage. XML retains both stock layouts for SPFT v6 table compatibility.")
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

    shutil.copy2(flash_src, out / "download_agent" / "flash.xml")
    shutil.copy2(da_src, out / "download_agent" / "DA_BR.bin")
    shutil.copy2(xsd_src, out / "download_agent" / "flash.xsd")
    copy_tree_if_exists(stock / "DB", out / "DB")

    tree = ET.parse(scatter_src)
    root = tree.getroot()

    enabled_by_layout: dict[str, set[str]] = {name: set() for name in STOCK_STORAGE_LAYOUTS}
    seen_by_layout: dict[str, set[str]] = {name: set() for name in STOCK_STORAGE_LAYOUTS}

    for storage_node in root.findall("storage_type"):
        storage_name = storage_node.get("name", "")
        expected_storage_value = STOCK_STORAGE_LAYOUTS.get(storage_name)

        for part_node in storage_node.findall("partition_index"):
            part_name = text(part_node, "partition_name")
            storage_value = text(part_node, "storage")

            # Default safe: every partition is disabled first. This disables
            # preloader, userdata, metadata, identity/calibration partitions,
            # B-slot partitions, and everything else not explicitly selected.
            if part_node.find("file_name") is not None:
                set_text(part_node, "file_name", "NONE")
            if part_node.find("is_download") is not None:
                set_text(part_node, "is_download", "false")

            # Mirror the stock firmware's dual-storage presentation: the same
            # selected image filenames exist in both EMMC and UFS branches.
            # SPFT/DA selects the physically present storage after connection.
            if (
                expected_storage_value is not None
                and storage_value == expected_storage_value
                and part_name in IMAGE_MAP
            ):
                _, dst_name = IMAGE_MAP[part_name]
                set_text(part_node, "file_name", dst_name)
                set_text(part_node, "is_download", "true")
                enabled_by_layout[storage_name].add(part_name)
                seen_by_layout[storage_name].add(part_name)

    required = set(IMAGE_MAP)
    for layout in STOCK_STORAGE_LAYOUTS:
        missing = sorted(required - seen_by_layout[layout])
        if missing:
            raise RuntimeError(
                f"{layout} XML scatter missing required partitions: " + ", ".join(missing)
            )
        if enabled_by_layout[layout] != required:
            raise RuntimeError(
                f"Unexpected enabled set for {layout}: " + ", ".join(sorted(enabled_by_layout[layout]))
            )

    indent_xml(root)
    scatter_out = out / "MT6789_Android_scatter.xml"
    tree.write(scatter_out, encoding="utf-8", xml_declaration=True)

    for part, (src_name, dst_name) in IMAGE_MAP.items():
        shutil.copy2(project / src_name, out / dst_name)

    checksum_note = """scatter_checksum.xml intentionally NOT copied.

The stock checksum file contains ADD checksums for the original stock images.
Using it with this custom package would be incorrect.

For a fully stock-style distribution, regenerate scatter_checksum.xml AFTER
this directory is final using a MediaTek CheckSum Generate v6 tool compatible
with XML scatter packages. Do not reuse the original stock checksum values.

The package can be inspected in SP Flash Tool v6 by selecting:
  download_agent/flash.xml

Use Download Only.

The official stock XML contains both EMMC and UFS layouts. This custom XML
retains the same eight selected image entries in BOTH layouts so SP Flash Tool
can populate its image table before the DA identifies the actual device
storage. The tested tablet is UFS (/dev/block/sdc60), so the DA will use the
UFS branch when connected.

Only these partition names have image files enabled in either layout:
  vbmeta_a
  vbmeta_system_a
  vbmeta_vendor_a
  lk_a
  boot_a
  vendor_boot_a
  dtbo_a
  super

Preloader, userdata, and every other partition remain disabled in both layouts.
"""
    (out / "REGENERATE-SCATTER-CHECKSUM.txt").write_text(checksum_note, encoding="utf-8")

    notes = """Alldocube iPlay 50 mini Pro custom Android 16/KPOC/AVB package
SP Flash Tool v6 stock-style Download-XML layout

Load in SP Flash Tool v6:
  download_agent/flash.xml

Mode:
  Download Only

Tested device physical storage:
  UFS (/dev/block/sdc60)

Stock-compatible XML presentation:
  EMMC and UFS branches both contain the same eight selected image entries.
  SP Flash Tool / DA resolves the actual storage at device connection time.

Enabled partition names:
  vbmeta_a
  vbmeta_system_a
  vbmeta_vendor_a
  lk_a
  boot_a
  vendor_boot_a
  dtbo_a
  super

Explicitly not flashed in either layout:
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

Before distribution, regenerate scatter_checksum.xml for these final files
using a MediaTek CheckSum Generate v6 utility. Never reuse the stock checksum.
"""
    (out / "FLASHING-NOTES.txt").write_text(notes, encoding="utf-8")

    manifest_paths = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            manifest_paths.append(p)
    lines = [f"{sha256_file(p)}  {p.relative_to(out).as_posix()}" for p in manifest_paths]
    (out / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Created stock-style SP Flash Tool v6 package:", out)
    print("Download-XML:", out / "download_agent" / "flash.xml")
    print("Scatter XML:", scatter_out)
    print("Actual tested device storage: UFS")
    print("Enabled image entries in EMMC:", ", ".join(sorted(enabled_by_layout["EMMC"])))
    print("Enabled image entries in UFS:", ", ".join(sorted(enabled_by_layout["UFS"])))
    print("IMPORTANT: regenerate scatter_checksum.xml before calling the package final.")


if __name__ == "__main__":
    main()
