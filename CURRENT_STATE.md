# Current state — 2026-09-01 project handoff

## Status summary

The project reached the bootloader relock stage after successfully validating the custom Android 16/AVB/LK stack on hardware.

### PROVEN-HARDWARE before final relock

The tablet booted with:

- Android release `16`
- SDK `36`
- slot suffix `_a`
- bootloader unlocked at the time of the test
- `ro.boot.verifiedbootstate=orange` (expected while unlocked)
- `ro.boot.vbmeta.device_state=unlocked`
- `ro.boot.flash.locked=0`
- `ro.boot.veritymode=enforcing`
- `/product -> /system/product`
- `/vendor` and `/vendor_dlkm` mounted through device-mapper

The exact runtime VBMeta values were:

```text
ro.boot.vbmeta.hash_alg=sha256
ro.boot.vbmeta.size=9536
ro.boot.vbmeta.digest=2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898
```

Offline:

```text
avbtool calculate_vbmeta_digest --hash_algorithm sha256 --image vbmeta.img
2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898
```

The values matched exactly.

### Slot state immediately before lock

```text
current-slot: a
slot-successful:a: yes
slot-unbootable:a: no
slot-retry-count:a: 1
slot-successful:b: no
slot-unbootable:b: no
slot-retry-count:b: 7
```

### Final lock operations captured

```text
fastboot flashing lock
(bootloader) Start lock flow
OKAY

fastboot getvar unlocked
unlocked: no

fastboot flashing lock_critical
(bootloader) Start lock flow
OKAY

fastboot reboot
OKAY
```

The user reported “ran no problems for now”.

## Pending proof item

The session did **not yet record post-relock Android properties after the final reboot**. Therefore these expected values remain to be captured:

```text
ro.boot.verifiedbootstate       expected green
ro.boot.vbmeta.device_state     expected locked
ro.boot.flash.locked            expected 1
ro.boot.veritymode              expected enforcing
ro.boot.vbmeta.hash_alg         expected sha256
ro.boot.vbmeta.size             expected 9536
ro.boot.vbmeta.digest           expected 2acf48ae...31898
```

Why GREEN is expected: the custom AVB root was not enrolled as a user key. Its RSA modulus replaced LK's built-in trusted OEM modulus. From LK/libavb's point of view, the custom top root should therefore be the built-in trusted root.

Update this file when the locked runtime properties are captured.

## Final deployment directory used during the project

Windows:

```text
E:\alldocube_logo_work\LOCKED-AVB-TEST-01
```

See `manifests/artifacts.yaml` for hashes and sizes.
