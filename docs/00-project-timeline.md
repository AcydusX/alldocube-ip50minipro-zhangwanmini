# Project timeline

## 2026-08-28 — stock firmware / boot image groundwork

- Stock firmware tree `iPlay50_mini_Pro_V1.0_20260302` became the baseline.
- Boot, vendor_boot, LK, scatter, vbmeta, and dynamic partition layout were inspected.
- GENA 1.4 was reverse-engineered rather than blindly flashed.
- TWRP/vendor_boot behavior and powered-off charging became a major investigation topic.

## 2026-08-29 — KPOC, TWRP, SELinux, GSI integration

- Compared stock vendor_boot v4 and GENA `OS2-TWRP-v2.1.img`.
- Proven that TWRP PLATFORM was a minimal first-stage ramdisk missing stock charger userspace, policy, UI resources, fstab, and KPOC/display kernel modules.
- Explored hybrid TWRP + stock KPOC designs and size constraints.
- Built static KPOC/TWRP candidates, including Tier-A, without making them the final production stack.
- Integrated KPOC runtime and SELinux bridging into GSI experiments.
- Deepened LK/KPOC boot-mode tracing around `/chosen/atag,boot`.

## 2026-08-30 — TWRP/KPOC candidate refinement

- Refined candidate vendor_boot layouts and DTB choices.
- Static re-unpack/revalidation used to prove only intended vendor ramdisk regions changed.
- Final project direction increasingly favored preserving stock-derived KPOC vendor_boot rather than forcing TWRP into the final locked stack.

## 2026-08-31 — vendor / KeyMint hybrid and locked-boot feasibility

- Built stock-derived vendor hybrids using generic KeyMint service behavior for GSI compatibility.
- Disabled conflicting TrustKernel service startup in hybrid test paths while keeping required SELinux labels.
- Android 17 work informed FBE/KPOC behavior, but Android 16 was selected as final due compatibility/WebView behavior.
- Began stock AVB and MediaTek LK trust-root reverse engineering.
- Proved stock LK would not accept an arbitrary custom top AVB key while locked.

## 2026-09-01 — custom root, AVB reconstruction, hardware validation, relock

- `mtk-lk-tools` validation showed the stock LK/preloader certificate chain matched the tool's bundled MediaTek signing keys.
- Located LK's 256-byte OEM AVB modulus at `lk/data.bin+0xA5650`.
- Generated a custom RSA-2048 AVB root.
- Patched only the LK modulus and re-signed the LK container.
- Built `ALldocube-LK-CUSTOM-AVB-01.img` and revalidated it.
- Determined system/vendor logical partitions were exactly full.
- Used fastbootd/lpdump to establish real dynamic-partition and group capacity.
- Enlarged `system_a` and `vendor_a` rather than shrinking the filesystems.
- Added new SHA-256 AVB hashtrees to system/vendor.
- Built custom `vbmeta_system`, `vbmeta_vendor`, and top-level `vbmeta`.
- Regenerated vendor_boot direct-hash descriptor for the KPOC image's true structural size `0x170B000`.
- Parsed stock `super.unsparse.img` metadata and extracted stock `odm_dlkm` / `vendor_dlkm` for offline verification.
- Removed unused stock product descriptor after proving `/product -> /system/product` on the GSI.
- Complete offline AVB graph verified.
- Hardware boot with custom AVB payloads while unlocked succeeded.
- Hardware boot with custom re-signed `lk_a` while unlocked succeeded.
- Runtime VBMeta digest matched offline digest exactly.
- Slot A was successful and bootable.
- `fastboot flashing lock` succeeded.
- `fastboot flashing lock_critical` succeeded.
- Final reboot command succeeded; post-relock Android property capture remains to be recorded.
