# Hardware validation and relock sequence

## Gate 1 — AVB payloads while unlocked

The device was kept unlocked while flashing:

- final AVB `system_a`
- final AVB `vendor_a`
- custom `vbmeta_system_a`
- custom `vbmeta_vendor_a`
- custom top `vbmeta_a`

Boot result:

```text
sys.boot_completed=1
Android 16
SDK 36
slot _a
verifiedbootstate orange
vbmeta.device_state unlocked
flash.locked 0
veritymode enforcing
```

`orange` was expected because the bootloader was unlocked.

## Gate 2 — custom LK while unlocked

Fastboot established:

```text
current-slot a
has-slot:lk yes
lk_a size 0x400000 raw
lk_b size 0x400000 raw
unlocked yes
```

Only `lk_a` was flashed with the custom re-signed LK. `lk_b` was intentionally left stock during this gate.

Android booted successfully again with the same expected unlocked properties and `veritymode=enforcing`.

## Gate 3 — runtime VBMeta digest

Device:

```text
hash_alg sha256
size 9536
digest 2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898
```

Offline `avbtool calculate_vbmeta_digest` returned the exact same digest.

This is the strongest proof in the session that the tablet loaded the exact custom root + chained metadata set.

## Gate 4 — slot health

Before lock:

```text
current-slot a
slot-successful:a yes
slot-unbootable:a no
slot-retry-count:a 1
```

## Relock

Because the user had run both normal unlock and `unlock_critical` historically, both lock flows were restored:

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

## Expected post-lock result

Expected but not yet captured in the source session:

```text
ro.boot.verifiedbootstate=green
ro.boot.vbmeta.device_state=locked
ro.boot.flash.locked=1
ro.boot.veritymode=enforcing
ro.boot.vbmeta.hash_alg=sha256
ro.boot.vbmeta.size=9536
ro.boot.vbmeta.digest=2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898
```

Do not rewrite history: GREEN remains expected until a post-relock property dump is committed.
