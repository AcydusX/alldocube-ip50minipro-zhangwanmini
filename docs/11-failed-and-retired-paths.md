# Failed, incomplete, or retired paths

This file exists so AI agents do not repeat work already disproven.

## RETIRED: “TWRP should preserve KPOC automatically”

False for GENA's `OS2-TWRP-v2.1.img`. Its PLATFORM fragment lacked the stock charger runtime, policy, images, fstab, and modules.

## RETIRED: full stock PLATFORM + full TWRP RECOVERY fits 64 MiB

False as packaged. Historical size accounting exceeded vendor_boot by about 9.3 MiB.

## INCOMPLETE: TWRP Tier-A KPOC hybrid

Statically validated but not the final hardware/locked solution. Keep as an experiment.

## RETIRED: arbitrary custom top vbmeta + unmodified stock LK while locked

Disassembly proved stock LK's validator only marks the top key trusted if its 256-byte RSA modulus matches LK's built-in modulus.

## RETIRED: shrink final system/vendor first to make room for AVB

Not needed. Super/group capacity was ample. Logical partitions were enlarged safely.

## RETIRED: preserve stock `product` descriptor in final custom vbmeta_system

It failed offline verification against the extracted stock product image, and runtime proved the Android 16 GSI uses `/product -> /system/product` with no separate product mount. Final `vbmeta_system` contains only `system`.

## RETIRED: assume fastbootd `fetch` works

Device returned:

```text
Unable to get max-fetch-size. Device does not support fetch command.
```

ADB block reads also failed under production adbd due permission restrictions, and `adb root` was unavailable. Stock super was therefore parsed/extracted offline.

## RETIRED: rely on `/sys/block/dm-*` from unprivileged ADB for sizes

This Android build did not expose the expected sysfs information to the shell. Fastbootd partition-size variables and `lpdump` were used instead.

## HISTORICAL: Android 17 as final baseline

Android 17 experiments were valuable for KPOC/FBE/vendor understanding, but Android 16 was selected as the final system baseline because it produced a cleaner compatibility/WebView result.
