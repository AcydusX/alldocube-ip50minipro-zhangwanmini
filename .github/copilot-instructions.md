# AI coding/engineering instructions

This repo documents a hardware-specific Android/MediaTek firmware project. Read `AGENTS.md` and `CURRENT_STATE.md` before proposing changes.

Never:

- commit private AVB PEM/key material,
- assume TWRP belongs in the final locked stack,
- modify preloader without an explicit new investigation,
- re-add the stock product descriptor to final `vbmeta_system`,
- disable AVB verification for a final locked build,
- change a known-good artifact without updating manifests/hashes and its dependent AVB descriptors.

Use evidence labels: PROVEN-HARDWARE, PROVEN-OFFLINE, STATIC-EVIDENCE, HYPOTHESIS, RETIRED.

Prefer bounded, verifiable steps and preserve rollback artifacts.
