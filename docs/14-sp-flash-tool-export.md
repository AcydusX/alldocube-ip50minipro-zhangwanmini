# SP Flash Tool export

## Goal

Produce a ZIP-able SP Flash Tool package representing the final project stack without shipping the entire stock firmware package.

## Critical dynamic-partition detail

`system_a`, `vendor_a`, `vendor_dlkm_a`, and `odm_dlkm_a` are logical partitions inside physical `super`.

SP Flash Tool normally writes the physical `super` partition. Therefore the fastbootd logical images in `LOCKED-AVB-TEST-01` are **not sufficient by themselves** for an SPFT package. The package needs a final physical `super.img` containing the actual resized logical layout and project payloads.

## Preferred method: capture the working physical super

Because the device already has the tested project contents installed, the least ambiguous export is an SP Flash Tool **Readback** of the current physical `super` partition.

Use the original Alldocube stock scatter as the authoritative source of:

- `super` `physical_start_addr`
- `super` `partition_size`
- storage region (`EMMC_USER`)

Create a Readback entry covering exactly this range and save it as `super-current.raw`.

This produces a byte-for-byte snapshot of the complete physical super metadata and data as installed on the working tablet, including the resized `system_a` and `vendor_a` layout.

### Optional sparse conversion

The physical super partition is 9,663,676,416 bytes. A raw readback is therefore large.

If Android sparse tools are available, convert it:

```bash
img2simg super-current.raw super.img
```

A sparse image is dramatically easier to archive when most of the physical super region is unused. SP Flash Tool can normally consume Android sparse partition images and reconstruct the expanded physical contents during flashing.

Do not use filesystem compression or ordinary sparse-file semantics as a substitute for Android sparse format; use `img2simg`.

## Other physical partitions in the project package

The deployment directory `LOCKED-AVB-TEST-01` already contains the physical images required for slot A:

- `boot_a.img`
- `dtbo_a.img`
- `vendor_boot_a.img`
- `vbmeta_a.img`
- `vbmeta_system_a.img`
- `vbmeta_vendor_a.img`
- `lk-custom-avb.img` (renamed to `lk_a.img` in the SPFT package)

The final physical `super.img` replaces the need to separately provide logical `system_a`, `vendor_a`, `vendor_dlkm_a`, and `odm_dlkm_a` to SP Flash Tool.

## Package builder

Use [`scripts/build_spft_package.py`](../scripts/build_spft_package.py).

Windows example:

```bat
py scripts\build_spft_package.py ^
  --stock-dir "E:\alldocube_logo_work\iPlay50_mini_Pro_V1.0_20260302" ^
  --deploy-dir "E:\alldocube_logo_work\LOCKED-AVB-TEST-01" ^
  --super "E:\alldocube_logo_work\SPFT-SNAPSHOT\super.img" ^
  --out "E:\alldocube_logo_work\SPFT-A16-KPOC-LOCKED-01"
```

The script:

1. finds the stock MediaTek scatter,
2. validates that every project image fits the stock physical partition size,
3. copies the project images into one directory,
4. copies `lk-custom-avb.img` as `lk_a.img`,
5. installs the supplied `super.img`,
6. creates a project scatter in which only project partitions have `is_download: true`,
7. sets all unrelated scatter entries to `file_name: NONE` and `is_download: false`, and
8. writes `SHA256SUMS.txt` and `FLASHING-NOTES.txt`.

## Enabled partitions

The generated project scatter enables only:

```text
lk_a
boot_a
dtbo_a
vendor_boot_a
vbmeta_a
vbmeta_system_a
vbmeta_vendor_a
super
```

`lk_b` remains untouched. This preserves the stock LK B-slot state rather than silently changing both bootloader slots.

## SP Flash Tool mode

Use:

```text
Download Only
```

Do **not** use:

```text
Format All + Download
```

Formatting can erase calibration/NVRAM/NVDATA/device-specific data unrelated to this project.

The project package intentionally excludes preloader. Do not enable or replace preloader merely to install this project build.

## Recovery package

Keep the complete original Alldocube firmware/scatter separately. The project package is a targeted project-stack installer, not a replacement for the complete factory-recovery archive.
