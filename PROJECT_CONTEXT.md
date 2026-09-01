# Complete project context

## 1. Starting point

The project began with an Alldocube iPlay 50 mini Pro running stock MediaTek firmware and the goal of using a modern official Google GMS Generic System Image without losing device-specific behavior.

The stock baseline used throughout the final work was:

```text
E:\alldocube_logo_work\iPlay50_mini_Pro_V1.0_20260302
```

Important stock facts:

- product/board: `tb8781p1_64`
- SoC: MT6789
- stock vendor Android SDK/API base: 31
- dynamic partitions: enabled
- A/B/virtual A/B metadata present
- stock Android generation: Android 13 framework fingerprint with vendor reporting release 12 / SDK 31 in vendor properties
- vendor security patch: 2026-01-05

The bootloader was unlocked early in the work. The user also stated that `fastboot flashing unlock_critical` had been run long before the final relock stage. The exact original unlock transcript is not part of the final session, but later fastboot consistently reported `unlocked: yes`, and the LK binary contains the standard MediaTek unlock flow strings.

SP Flash Tool recovery was available to the user and was treated as a last-resort recovery route. The project deliberately avoided modifying the preloader.

## 2. GENA 1.4 and TWRP

GENA 1.4 was reverse-engineered as a legacy TWRP/recovery flashable package for this MT6789/MT8781 layout. It prepared the device for GSI use by replacing top-level vbmeta images, both vendor_boot slots, and the physical super layout. It also contained optional DFE/fstab modifications and selectable boot images in its original flow.

A key GENA artifact was:

```text
OS2-TWRP-v2.1.img
size: 67,108,864
SHA-256: 4400212a23c32e097d12c31bbc8c7364c767546ebe80503f72de53af0240a6cb
```

Stock `vendor_boot.img`:

```text
size: 67,108,864
SHA-256: 2c2e0ccc037515120f1ab423d35b6b9ccb6672d5d976d40ff53488aefcc592e8
```

Both are vendor_boot v4 images.

The TWRP image's PLATFORM fragment was found to be intentionally tiny: about 2,210,767 compressed bytes and only 22 filesystem entries, essentially first-stage tooling (`e2fsck`, `linker64`, and needed libraries). It did not contain the stock charger startup path, charger binary, SELinux policy, charging animation resources, fstab, or the stock charging/display modules.

The stock PLATFORM fragment was about 23,877,267 bytes and contained the stock offline-charging environment, including charger userspace, policy, image resources, and many MediaTek kernel modules.

This explained why replacing stock `vendor_boot` with the GENA TWRP image could result in a black/no powered-off charging UI.

### TWRP hybrid work

Several strategies were studied:

- Add the required stock KPOC closure to the TWRP PLATFORM fragment.
- Use stock PLATFORM plus TWRP RECOVERY.
- Use stock PLATFORM plus a trimmed TWRP recovery overlay.
- Use stock DTB with candidate TWRP/KPOC variants.

A Tier-A hybrid was built and statically validated at:

```text
E:\alldocube_logo_work\analysis\GENA-1.4-TWRP-KPOC-TierA.img
```

Known properties:

- size 67,108,864
- PLATFORM compressed size 9,063,962
- PLATFORM decompressed size 17,541,892
- corrected `vendor_ramdisk_size` 61,419,520
- TWRP RECOVERY and relevant unchanged regions were kept byte-identical in that build
- static validation passed
- it was not part of the final locked stack

Do not invent or reuse a hash for this Tier-A image unless it is freshly calculated; one historical note contained a placeholder-looking hash and must not be treated as authoritative.

## 3. KPOC / powered-off charging investigation

KPOC = MediaTek Kernel Power-Off Charging / charger-mode path used when a powered-off device is connected to a charger.

Two layers of failure were investigated:

1. **TWRP vendor_boot user-space closure problem:** TWRP PLATFORM lacked the charger runtime, policy, resources, and modules.
2. **Boot-mode propagation investigation:** deeper reverse engineering showed failed cases where BL2_EXT saw charger/boot reason information but main LK still reached `lk boot mode = 0`. `set_fdt_atag_boot()` writes LK's selected boot mode into `/chosen/atag,boot`, and Linux vendor modules parse that exact structure. This proved there was no later mode-8-to-mode-0 conversion inside Linux in those traces.

A significant reverse-engineering conclusion was that some KPOC failures were upstream of Android userspace and could not be fixed solely by adding animation resources.

The final practical stack avoided the TWRP PLATFORM problem by using a stock-derived KPOC-compatible vendor boot:

```text
STOCK-VENDOR_BOOT-GSI-MIN-KPOC.img
size: 67,108,864
SHA-256: 720e38b23e861b51320374538d57046a425bd3ca6a5e07679c202dce7bc9f20b
```

Its vendor_boot v4 structural used size was later measured as `24,162,304` (`0x170B000`) bytes, with the remainder of the 64 MiB file zero-filled. The stock structural used size was `24,059,904` (`0x16F2000`). Therefore the stock top-level vendor_boot AVB descriptor could not be reused and a new direct hash descriptor was generated.

## 4. Android GSI progression

Earlier Android 17 work was used to understand KPOC, SELinux, FBE, and vendor compatibility. The Android 17 Hybrid03 path demonstrated KPOC + FBE in earlier testing, but Android 17 also exposed compatibility problems such as WebView/native ABI issues.

The final base moved to the official Android 16 QPR2 GMS GSI:

```text
E:\alldocube_logo_work\gsi_gms_arm64-exp-BP4A.251205.006-14401865-f8760221
```

Build identity observed on hardware:

```text
ro.system.build.fingerprint=google/gsi_gms_arm64/gsi_arm64:16/BP4A.251205.006/14401865:user/release-keys
ro.system.build.version.release=16
ro.system.build.id=BP4A.251205.006
ro.system.build.version.incremental=14401865
ro.build.version.security_patch=2025-12-05
```

The final KPOC-modified Android 16 filesystem image before AVB was:

```text
KPOC-GSI-ANDROID16-CANDIDATE-01.img
size: 3,301,928,960
SHA-256: 1750acea56b33cbc36c6a0e640da9840f2ffb2c356bb3be13f058ea685622d3d
```

The original Android 16 image SHA-256 before KPOC modification was:

```text
f84a70818343b336004c900a98194139ca210e7ad24bdd1af89b55db28b629e8
```

Filesystem UUID:

```text
192edea5-f29a-51c0-8444-39d224df34ea
```

The original filesystem had ext4 `shared_blocks`. It was unshared and expanded during the KPOC build. Important geometry:

- original ext4 data length: 3,249,741,824
- original image length: 3,301,928,960
- original tail: 52,187,136 bytes (~49.77 MiB)
- final ext4 block count: 806,135 at 4096 bytes/block
- final e2fsck usage: 798,808 / 806,135 blocks

This detail later explained why the system logical partition initially had zero room left for AVB metadata: the old ~49.77 MiB tail had been absorbed into the enlarged filesystem.

## 5. Android-side KPOC integration

The KPOC candidate integrated a MediaTek charger userspace/runtime into the GSI and added SELinux compatibility needed by the stock vendor interface.

Key classes of injected/modified content included:

- `/system/bin/kpoc_charger`
- KPOC init rc
- `libshowlogo`
- Android health NDK library
- patched `libsuspend`
- `libkpoc`
- `system_ext` SELinux policy additions
- `mapping/31.0.cil` bridge for `kpoc_charger`
- file contexts for `kpoc_charger` and `/dev/csci`

The KPOC SELinux domain was given the device, sysfs, graphics, input, battery, power, RTC, kmsg, uevent, and other accesses needed by the MediaTek charger path. The combined Android 16 policy compiled against the stock vendor with `secilc exit=0` in the successful static validation.

Android 16 hardware testing later confirmed normal boot and fixed the Android 17 WebView/native ABI problem. Observed WebView:

```text
com.google.android.webview 134.0.6998.135
versionCode 699813532
targetSdk 35
```

Do not automatically claim every Android 16 runtime feature was retested if the session did not capture it. Keep KPOC electrical/UI testing, FBE, Google login, and WebView as separate validation items.

## 6. Vendor / KeyMint hybrid

A stock-derived vendor was modified to provide a GSI-compatible generic KeyMint service instead of relying solely on the stock TrustKernel path.

The generic service work included:

```text
/vendor/bin/hw/android.hardware.security.keymint-service
service vendor.keymint-default /vendor/bin/hw/android.hardware.security.keymint-service
    class early_hal
    user nobody
```

Historical KeyMint service binary hash:

```text
6a96ad12371a0e272a4d47610c9de85c02543067146e93846ec6048fd63a7aa7
```

The TrustKernel rc was disabled for the GSI hybrid test while SELinux labels were preserved/applied appropriately.

The final vendor payload used for Android 16/locked AVB work was:

```text
STOCK-VENDOR-KEYMINT-HYBRID-03-NOAVB.img
size: 1,067,798,528
SHA-256: e25c3bf669a5d4599de07cedaefada3b181731b7ab3c1d257c102a1b55279486
```

It intentionally had no old AVB footer/tree and was later given a new custom-key dm-verity hashtree.

## 7. Stock AVB chain

Stock top-level AVB:

- algorithm: SHA256_RSA2048
- rollback index: 0
- flags: 0
- top public key SHA-1: `cdbb77177f731920bbe0a0f94f84d9038ae0617d`

Chains:

```text
boot           rollback location 3  key sha1 9d808b0995768d0677fccb1efcddb7cf9e153d99
vbmeta_system  rollback location 2  key sha1 fa41159a5d696abdef93176a07d0b0d001263f01
vbmeta_vendor  rollback location 4  key sha1 9577bc6c0772975ecce93c4d8a178662c728dadf
```

Top direct/preserved descriptors:

- `dtbo` direct hash, stock image data size 62,720
- `vendor_boot` direct hash, stock meaningful data size 24,059,904
- `odm_dlkm` stock hashtree + FEC
- `vendor_dlkm` stock hashtree + FEC

Stock `vbmeta_system` covered separate `product` and `system` dynamic partitions. In the final GSI runtime, `/product` was proven to be a symlink to `/system/product`, with no separate `/product` mount. The stock `product` descriptor was therefore removed from the custom `vbmeta_system` rather than forcing verification of an unused logical product partition.

## 8. MediaTek LK reverse engineering

Stock LK image:

```text
lk.img
size: 2,163,920
SHA-256: 0361e41ac22c455068f7f4c2125b35771b7c3b7f740bec47bb11bb244b64928c
```

`mtk-lk-tools` (`TheGammaSqueeze/mtk-lk-tools`) plus `liblk` from `R0rt1z2/liblk` was used to unpack and validate the MediaTek container.

The stock LK unpack contained four signed partitions:

- `lk/data.bin` 678,128 bytes
- `bl2_ext/data.bin` 542,680
- `aee/data.bin` 756,392
- `lk_main_dtb/data.bin` 169,669

A critical discovery: the repo's bundled MediaTek test root/image signing keys matched the stock image certificates. `lk-check` showed the bundled root and image public keys matched all four partitions, and preloader signature verification also succeeded against the same tool keys. This made it possible to modify only LK and re-sign it without modifying preloader.

### Locked-key validator

Disassembly of the LK public-key validator proved that, while locked, an arbitrary custom top-level AVB key would not be accepted by stock LK.

The routine defaults `out_is_trusted=0`, compares 256 bytes of the vbmeta RSA modulus with LK's built-in modulus, and sets trusted to 1 only on exact equality.

The OEM modulus was located at:

```text
unpacked lk/data.bin offset 0xA5650
length 256 bytes
SHA-256 4ffc881faafb2d1af7dd40cfba4ca90464b4f5689ef7f4ec3a0fe7b741440688
```

The same modulus appeared exactly once inside stock `vbmeta.img` at file offset `0x1078`.

Therefore the chosen design was to replace LK's built-in OEM modulus with the project's custom AVB modulus, then re-sign the MediaTek LK container with the matching MediaTek image signing key.

## 9. Custom AVB key and custom LK

Custom RSA-2048 AVB key workspace:

```text
~/alldocube-locked-avb
```

Private key historical path (DO NOT COMMIT):

```text
~/alldocube-locked-avb/keys/alldocube-avb.pem
```

Private PEM file SHA-256 recorded during the project:

```text
fa4c20e4aae9ef9f7697a19a594e53f8995ce4890718e3362a88229633a759b2
```

AVB public key:

```text
size 520
SHA-256 b6abf2642a0cda00c4d7773b9d8a709abc44e5273f43a8e9b2a589b0452de6d1
SHA-1   86e98d4cc425d7a56ea1933ac5d40e4f9978586a
```

Custom modulus:

```text
size 256
SHA-256 d258ae705de48e1f6f257564a40b24b697fec418a4868fcc5c292faa43fa8f3a
n0inv 0x949c3b95
```

Only `lk/data.bin[0xA5650:0xA5750]` was replaced. Prefix/suffix checks proved there were no differences outside the target 256-byte modulus region; 254 byte positions actually changed because 2 happened to match.

Final custom LK:

```text
ALldocube-LK-CUSTOM-AVB-01.img
size 2,163,920
SHA-256 b1d89c6139757cbd67c25007e9f8a48fbaee57b7d15d0f5a5a74aed20bd2e542
```

Re-unpack and `lk-check` verified all container hashes/signatures after repack.

## 10. Dynamic partition resizing

Fastbootd originally reported:

```text
system_a       0xC4CF7000 = 3,301,928,960
system_b       0x09129000
product_a      0x96C39000 = 2,529,398,784
vendor_a       0x3FA55000 = 1,067,798,528
vendor_dlkm_a  0x02508000 = 38,830,080
odm_dlkm_a     0x00055000 = 348,160
super          0x240000000 = 9,663,676,416
```

`lpdump` from Android showed metadata 10.2, virtual A/B, group `main_a` maximum size 9,661,579,264, no active snapshot/update state.

The Android 16 system and Hybrid03 vendor each exactly filled their logical partition. AVB sizing showed the filesystem/image was too large for the old partition sizes.

Instead of shrinking the filesystems, the partitions were enlarged to the exact required stock-style-with-FEC planning sizes:

```text
system_a -> 3,354,951,680 = 0xC7F88000
vendor_a -> 1,085,009,920 = 0x40ABF000
```

The device booted normally after resize.

The final custom AVB payloads were then built without FEC (`--do_not_generate_fec`), leaving extra margin while retaining the SHA-256 dm-verity hashtrees.

## 11. Final AVB payloads

System hashtree:

```text
Original image size  3,301,928,960
Tree offset          3,301,928,960
Tree size               26,005,504
FEC roots                        0
Root digest ae655bf10df2fafe8819325e5ba172da37e8bacde867926345fa58718c5b5e36
```

Vendor hashtree:

```text
Original image size  1,067,798,528
Tree offset          1,067,798,528
Tree size                8,413,184
FEC roots                        0
Root digest d336d3a125eccbfafd209dd7ec11a8e0b6a775b58851a4a88cfd0e05a691a0ef
```

Both passed `avbtool verify_image` against the custom key.

Custom `vbmeta_system` was rebuilt cleanly with only the `system` descriptor after runtime proved `/product` was `/system/product`.

Custom `vbmeta_vendor` contains only the new vendor descriptor plus inherited informational props.

### KPOC vendor_boot descriptor

The modified vendor_boot's structural used size was exactly:

```text
24,162,304 = 0x170B000
```

A descriptor-only vbmeta was generated against that range. The resulting direct hash descriptor:

```text
Partition Name: vendor_boot
Image Size: 24162304
Hash Algorithm: sha256
Salt: 738ceb3f2490f74f773d1a26a76463e0c7e6fa31f48a513bf94ea174916addc8
Digest: b985daa0ba256af9446d611c5d6acef9d8625bc72a557d9035d4535053576a4a
```

It was verified against the actual 64 MiB KPOC vendor_boot file.

## 12. Final top-level custom VBMeta

Custom top:

```text
size 8192
SHA-256 04d561a8bff4515d321e8bb83d214f410adf4ec0857aa3c36faea1380a64f64c
public key SHA-1 86e98d4cc425d7a56ea1933ac5d40e4f9978586a
algorithm SHA256_RSA2048
rollback 0
flags 0
```

Final descriptor graph:

```text
boot             -> stock boot key, rollback loc 3
vbmeta_system    -> custom key, rollback loc 2
vbmeta_vendor    -> custom key, rollback loc 4
dtbo             -> stock direct hash
vendor_boot      -> regenerated 24,162,304-byte direct hash
odm_dlkm         -> stock hashtree/FEC
vendor_dlkm      -> stock hashtree/FEC
```

Offline verification passed for the top-level signature, chain key bindings, dtbo, vendor_boot, odm_dlkm, and vendor_dlkm.

Stock `product_a` extracted from the stock `super.unsparse.img` did not match the stock product hashtree descriptor in `vbmeta_system`. Runtime then proved the GSI does not mount that logical product partition, so the final custom `vbmeta_system` removed the product descriptor entirely and passed full verification against the final system image.

## 13. Hardware gates

Hardware validation was deliberately staged:

1. Resize logical partitions; boot unchanged stack.
2. Flash AVB-bearing system/vendor and custom vbmeta children/top while bootloader remained unlocked.
3. Boot Android and confirm Android 16 + enforcing verity.
4. Flash custom `lk_a` only while unlocked; leave `lk_b` stock as fallback.
5. Boot Android again.
6. Compare runtime VBMeta digest with offline calculated digest.
7. Confirm slot A successful/not-unbootable.
8. Lock normal bootloader.
9. Lock critical partitions because the device had been `unlock_critical` earlier.

All gates through the lock commands completed without reported fastboot errors.

## 14. Final lock commands

```text
fastboot flashing lock
-> OKAY
fastboot getvar unlocked
-> no

fastboot flashing lock_critical
-> OKAY

fastboot reboot
-> OKAY
```

Post-lock Android properties still need to be captured and committed to this repo.
