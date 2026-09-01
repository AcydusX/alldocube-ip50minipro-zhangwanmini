# GENA 1.4, TWRP and powered-off charging (KPOC)

## GENA 1.4 role

GENA 1.4 was a legacy recovery-flashable package used to prepare this device family for GSI installation. Static analysis showed that it replaced major boot-critical content rather than merely installing a recovery app.

Relevant package behavior included:

- top-level vbmeta replacement,
- `vendor_boot_a` and `vendor_boot_b` replacement with TWRP-oriented vendor_boot,
- physical `super` replacement/re-layout for an A-oriented dynamic-partition GSI setup,
- optional DFE/fstab modifications,
- historical stock/Magisk/KSU boot selection paths.

This mattered because powered-off charging behavior was changed as a side effect of replacing vendor_boot.

## Stock vs GENA TWRP vendor_boot

### Stock

```text
vendor_boot.img
size 67108864
SHA256 2c2e0ccc037515120f1ab423d35b6b9ccb6672d5d976d40ff53488aefcc592e8
v4, page size 4096
DTB 169733 bytes
DTB SHA256 bf96db39a635371ac4b4aa1a6e8dae34ec9a0518c5ed8e7ae62c0805638ae789
```

### GENA TWRP

```text
OS2-TWRP-v2.1.img
size 67108864
SHA256 4400212a23c32e097d12c31bbc8c7364c767546ebe80503f72de53af0240a6cb
v4, page size 4096
DTB 169627 bytes
DTB SHA256 61196261ee5dd4a8c95342f1f80356e6d4d4d432e4186e345f7964bc484deec5
```

TWRP also adds recovery-oriented cmdline content including `androidboot.init_fatal_reboot_target=recovery` and `buildvariant=eng`.

## Why powered-off charging went black with TWRP

The TWRP PLATFORM ramdisk was proven to contain only a tiny first-stage environment. It lacked:

- charger executable/startup path,
- stock charger init service,
- KPOC userspace dependencies,
- stock SELinux charger policy,
- stock `res/images` charging assets,
- stock fstab,
- MediaTek charger/battery/PMIC/display/panel modules.

The stock PLATFORM ramdisk contained the full stock environment.

The old theory that a simple `/init` pathname collision explained the problem was retired. The more direct evidence was the absence of the required PLATFORM environment.

## Hybrid design constraints

Simply combining full stock PLATFORM and full TWRP RECOVERY did not fit in the 64 MiB vendor_boot partition. Historical size accounting showed the combined fragments plus fixed overhead exceeded the partition by roughly 9.3 MiB.

A minimal stock-derived KPOC closure could fit, but selecting a minimal module/user-space closure required evidence, not guessing.

## Tier-A candidate

A Tier-A TWRP/KPOC hybrid was built and statically validated:

```text
E:\alldocube_logo_work\analysis\GENA-1.4-TWRP-KPOC-TierA.img
```

- 64 MiB total
- PLATFORM compressed 9,063,962
- PLATFORM decompressed 17,541,892
- vendor_ramdisk_size corrected to 61,419,520
- TWRP RECOVERY and DTB regions retained according to that candidate design
- static validation PASS
- not part of final locked stack

## Final project decision

The final locked stack **does not keep TWRP installed**. It uses:

```text
STOCK-VENDOR_BOOT-GSI-MIN-KPOC.img
SHA256 720e38b23e861b51320374538d57046a425bd3ca6a5e07679c202dce7bc9f20b
```

This choice prioritizes known-good MediaTek KPOC/vendor-boot behavior. Future TWRP work should be treated as a separate branch/experiment rather than silently modifying the locked production baseline.
