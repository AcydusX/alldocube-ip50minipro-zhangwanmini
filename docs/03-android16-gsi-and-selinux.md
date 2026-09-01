# Android 16 GSI and KPOC/SELinux integration

## Base image

Official Google GMS GSI directory:

```text
E:\alldocube_logo_work\gsi_gms_arm64-exp-BP4A.251205.006-14401865-f8760221
```

Runtime identity:

```text
Android 16
SDK 36
BP4A.251205.006
incremental 14401865
google/gsi_gms_arm64/gsi_arm64:16/BP4A.251205.006/14401865:user/release-keys
security patch 2025-12-05
```

Original system image hash:

```text
f84a70818343b336004c900a98194139ca210e7ad24bdd1af89b55db28b629e8
```

Final KPOC filesystem image before AVB:

```text
KPOC-GSI-ANDROID16-CANDIDATE-01.img
size 3301928960
SHA256 1750acea56b33cbc36c6a0e640da9840f2ffb2c356bb3be13f058ea685622d3d
```

## Filesystem transformation

The original ext4 filesystem used `shared_blocks`. To modify it safely:

- unshare blocks,
- expand filesystem into the original image tail,
- install KPOC runtime/policy,
- e2fsck/verify.

Key size history:

```text
original ext4 bytes    3249741824
container image bytes  3301928960
old tail                 52187136
final fs blocks             806135 @ 4096
final used blocks            798808
```

That old tail later exactly matched the AVB capacity deficit of the fully expanded system image in the old logical partition.

## KPOC userspace integration

Project KPOC integration included:

- `kpoc_charger`
- KPOC init service configuration
- health NDK dependency
- `libshowlogo`
- patched `libsuspend`
- `libkpoc`
- matching SELinux executable type/domain
- access to graphics/input/sysfs/battery/power/RTC/kmsg/uevent/csci interfaces

Example file context additions:

```text
/system/bin/kpoc_charger  u:object_r:kpoc_charger_exec:s0
/dev/csci(/.*)?           u:object_r:csci_device:s0
```

Example system_ext compatibility mapping:

```text
(typeattributeset kpoc_charger_31_0 (kpoc_charger))
```

The final policy combination compiled with the stock vendor (`secilc exit=0`).

## `/product` behavior

On the final Android 16 GSI hardware boot:

```text
/product -> /system/product
```

There was no `/product` mount in `/proc/mounts`. This became important when rebuilding `vbmeta_system`: the separate logical `product_a` was not part of the mounted GSI product tree and its old stock AVB descriptor was removed from the custom child vbmeta.

## WebView result

Android 16 hardware boot showed a valid Google WebView package:

```text
com.google.android.webview 134.0.6998.135
versionCode 699813532
targetSdk 35
```

This avoided the native dual-ABI issue encountered during Android 17 experiments.
