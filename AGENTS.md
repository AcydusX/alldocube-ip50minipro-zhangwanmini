# AGENTS.md — mandatory context for AI/Hermes agents

## Mission

Maintain and extend the Alldocube iPlay 50 mini Pro engineering project without losing the evidence chain that led to the final Android 16 + KPOC + AVB + locked-bootloader design.

## Device identity

- Product: Alldocube iPlay 50 mini Pro
- Board/product: `tb8781p1_64`
- SoC reported by Android: MediaTek `MT6789`
- Family references encountered: MT6789 / MT8781
- Stock firmware baseline: `iPlay50_mini_Pro_V1.0_20260302`
- Vendor first API level: 31
- Dynamic partitions: yes
- Virtual A/B: yes

## Required read order

Before modifying anything, read:

1. `CURRENT_STATE.md`
2. `PROJECT_CONTEXT.md`
3. `manifests/artifacts.yaml`
4. `manifests/partition-layout.yaml`
5. the relevant document under `docs/`

## Evidence labels

Use these exact categories in future notes:

- **PROVEN-HARDWARE** — observed on the tablet.
- **PROVEN-OFFLINE** — cryptographically/static verified from images.
- **STATIC-EVIDENCE** — reverse-engineering evidence but not runtime tested.
- **HYPOTHESIS** — plausible but not proven.
- **RETIRED** — historical path that must not be reused without a new reason.

Do not upgrade a claim to PROVEN-HARDWARE unless there is an actual device observation.

## Non-negotiable safety/engineering rules

1. **Never commit or expose the private AVB key.** The historical private PEM was under `~/alldocube-locked-avb/keys/alldocube-avb.pem`. Only public metadata/hashes belong in Git.
2. **Do not modify the preloader.** The project deliberately avoided changing it.
3. **Do not flash random LK builds.** The only custom LK that passed the project validation is `ALldocube-LK-CUSTOM-AVB-01.img`, SHA-256 `b1d89c...d2e542`.
4. **Do not assume TWRP is part of the final stack.** It is not.
5. **Do not re-add the stock `product` hashtree descriptor to custom `vbmeta_system`.** Runtime proved `/product -> /system/product`; the separate logical `product_a` was not mounted by the Android 16 GSI.
6. **Do not use `--disable-verity` or `--disable-verification` for the final verified stack.** The successful hardware test had `ro.boot.veritymode=enforcing`.
7. **Do not shrink the final Android 16 system/vendor filesystems to make AVB fit.** The logical partitions were enlarged instead.
8. **Do not replace hashes from this repo by filenames alone.** Verify SHA-256 before flashing.
9. **Avoid command floods.** Work one bounded stage at a time, parse output, then continue.
10. **Preserve slot A unless there is a deliberate recovery plan.** The final work was on slot A; `lk_b` was intentionally left stock during the custom-LK hardware gate.

## Current high-value truth

- Android 16 booted with custom AVB-bearing `system_a` and `vendor_a` while unlocked.
- `ro.boot.veritymode=enforcing` was observed.
- Custom re-signed `lk_a` booted Android 16 successfully while unlocked.
- Runtime VBMeta digest exactly matched offline calculation.
- Slot A was reported `successful: yes`, `unbootable: no` before locking.
- `fastboot flashing lock` returned OKAY and `unlocked: no`.
- `fastboot flashing lock_critical` returned OKAY.
- Post-relock Android property verification is still a capture item unless a later commit updates `CURRENT_STATE.md`.

## Final intended trust graph

```text
stock preloader
    |
    v
custom re-signed MTK LK
  - OEM AVB modulus patched to custom RSA-2048 modulus
    |
    v
custom top vbmeta (custom key)
    |-- boot -> stock boot child key, rollback location 3
    |-- vbmeta_system -> custom key, rollback location 2
    |     `-- system Android 16 KPOC hashtree
    |-- vbmeta_vendor -> custom key, rollback location 4
    |     `-- vendor Hybrid03 hashtree
    |-- dtbo -> preserved stock direct hash
    |-- vendor_boot -> regenerated KPOC direct hash
    |-- odm_dlkm -> preserved stock hashtree
    `-- vendor_dlkm -> preserved stock hashtree
```

## If an agent proposes a change

It must answer:

- Which artifact changes?
- Which exact hash becomes obsolete?
- Which AVB descriptor must be regenerated?
- Does the custom top VBMeta need rebuilding?
- Does the LK embedded root need changing?
- Is the change testable while unlocked before relocking?
- What is the rollback artifact?

If the answer to these is unclear, stop and analyze before flashing.
