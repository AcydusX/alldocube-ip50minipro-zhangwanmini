# HERMES.md — agent bootstrap

This file is the shortest safe entrypoint for a Hermes agent taking over this project.

## First action

Read these files in order before proposing or executing changes:

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `PROJECT_CONTEXT.md`
4. `manifests/artifacts.yaml`
5. `manifests/avb-chain.yaml`
6. `manifests/partition-layout.yaml`
7. the relevant `docs/*.md`

## Current project truth

- Device: Alldocube iPlay 50 mini Pro, board `tb8781p1_64`, MediaTek MT6789/MT8781 family.
- Final tested OS lineage: official Google GMS Android 16 GSI, build `BP4A.251205.006`, SDK 36.
- Powered-off charging/KPOC was restored through a stock-derived KPOC-compatible vendor boot plus GSI-side KPOC compatibility work; the final stack is **not TWRP**.
- Vendor uses the final Hybrid03 KeyMint-compatible payload documented in `manifests/artifacts.yaml`.
- `system_a` and `vendor_a` were enlarged to fit real AVB hashtrees instead of shrinking the working filesystems.
- Final system/vendor use SHA-256 dm-verity hashtrees with FEC disabled.
- The top AVB root is a project RSA-2048 key. The private key is intentionally absent from Git.
- MediaTek LK was patched at its built-in OEM AVB modulus and re-signed using the signing chain accepted by this firmware family.
- The custom-LK + custom-AVB chain booted on hardware while unlocked, with `ro.boot.veritymode=enforcing`.
- Runtime VBMeta digest exactly matched the offline calculated digest: `2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898`.
- Slot A was successful and bootable before relock.
- `fastboot flashing lock` and `fastboot flashing lock_critical` both returned `OKAY`.
- The post-relock Android property dump was not captured in the source conversation at repository-generation time. Do **not** claim GREEN is hardware-proven until `CURRENT_STATE.md` is updated with that observation.

## Hard prohibitions

- Never request, print, upload, or commit the private AVB PEM.
- Never patch preloader as part of this established design.
- Never replace a verified artifact by filename alone; match SHA-256.
- Never reintroduce the stock `product` descriptor into `vbmeta_system`; `/product` resolved to `/system/product` in the final GSI runtime.
- Never use `--disable-verity` or `--disable-verification` as a shortcut for the final design.
- Never assume old GENA/TWRP candidates are production artifacts.

## Change protocol

For every proposed image change, state:

1. source artifact and current SHA-256;
2. exact bytes/files intended to change;
3. resulting partition-size requirement;
4. AVB descriptors that must be regenerated;
5. whether the top VBMeta changes;
6. whether LK trust material changes;
7. unlocked hardware-test plan;
8. rollback image and recovery path.

Work in bounded stages. Parse each command output before moving to the next stage.
