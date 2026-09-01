# Alldocube iPlay 50 mini Pro — GSI, KPOC, TWRP, Vendor/KeyMint, AVB & Locked Bootloader Engineering

This repository is the engineering handoff for the **Alldocube iPlay 50 mini Pro** (`tb8781p1_64`, MediaTek MT6789/MT8781 family) project performed during August–September 2026.

It is intentionally written for both humans and AI agents (Hermes, Codex, Claude, ChatGPT, etc.). It captures the path from bootloader unlocking and GENA/TWRP investigation through Android GSI compatibility, MediaTek powered-off charging (KPOC), vendor/KeyMint work, SELinux compatibility, dynamic-partition resizing, AVB reconstruction, MediaTek LK reverse engineering, custom AVB root-of-trust installation, hardware validation, and final bootloader relocking.

## Final project objective

Run an official Google GMS Android GSI on the iPlay 50 mini Pro while preserving the device-specific MediaTek behavior needed for:

- normal Android boot,
- Generic System Image compatibility,
- MediaTek powered-off/offline charging (KPOC) support,
- file-based encryption / KeyMint compatibility work,
- dm-verity / AVB enforcement,
- and ultimately a **locked bootloader using a custom AVB root trusted by a re-signed MediaTek LK**.

## Final known-good stack

| Component | Artifact | SHA-256 |
|---|---|---|
| Boot | stock `boot.img` | `e9a502385e79a7be9b69663fd056e09f86ed8fa6d582a2438be7de94cd82890d` |
| System payload before AVB | `KPOC-GSI-ANDROID16-CANDIDATE-01.img` | `1750acea56b33cbc36c6a0e640da9840f2ffb2c356bb3be13f058ea685622d3d` |
| System + AVB | `system_a.img` | `9777805e7815618b314f048fc2ea199e8f0acbb907dd1a96c3d7e0cfefad2941` |
| Vendor payload before AVB | `STOCK-VENDOR-KEYMINT-HYBRID-03-NOAVB.img` | `e25c3bf669a5d4599de07cedaefada3b181731b7ab3c1d257c102a1b55279486` |
| Vendor + AVB | `vendor_a.img` | `877c0748ccce4be7be58d4c14aec5b199945c4c5b770fc569a6134e9d411149b` |
| Vendor boot / KPOC | `STOCK-VENDOR_BOOT-GSI-MIN-KPOC.img` | `720e38b23e861b51320374538d57046a425bd3ca6a5e07679c202dce7bc9f20b` |
| `vbmeta_system` | custom | `2ebdc1347bd33876052d247285dba951130bc1f83f4e3963b44965505ad8a99a` |
| `vbmeta_vendor` | custom | `1eb4c94bd76ab7e82162f2275a287298c211d6e9ac1a33a8cfdba0903209120e` |
| Top `vbmeta` | custom root | `04d561a8bff4515d321e8bb83d214f410adf4ec0857aa3c36faea1380a64f64c` |
| LK | `ALldocube-LK-CUSTOM-AVB-01.img` | `b1d89c6139757cbd67c25007e9f8a48fbaee57b7d15d0f5a5a74aed20bd2e542` |

The runtime VBMeta digest observed **before relocking**, after booting through the custom LK and the complete custom AVB chain, exactly matched the offline `avbtool calculate_vbmeta_digest` result:

```text
sha256
size = 9536
digest = 2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898
```

This proved that the device was booting the exact custom root plus chained `boot`, `vbmeta_system`, and `vbmeta_vendor` structures built in this project.

## End state recorded in the session

The following commands completed successfully:

```text
fastboot flashing lock
fastboot getvar unlocked  -> no
fastboot flashing lock_critical
fastboot reboot
```

The user reported no immediate problem after the reboot command. **However, the post-relock Android property capture (`verifiedbootstate`, `flash.locked`, and runtime VBMeta digest after the final reboot) was not yet pasted into the project session when this repository was generated.** Treat GREEN-after-lock as the expected result, not as an already logged fact.

See [`CURRENT_STATE.md`](CURRENT_STATE.md).

## Read order for AI agents

1. [`AGENTS.md`](AGENTS.md)
2. [`CURRENT_STATE.md`](CURRENT_STATE.md)
3. [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md)
4. [`manifests/artifacts.yaml`](manifests/artifacts.yaml)
5. [`docs/00-project-timeline.md`](docs/00-project-timeline.md)
6. Relevant subsystem document in `docs/`

## Repository policy

Large firmware images and the private AVB signing key are **not committed**. The repository stores hashes, sizes, paths, build logic, and verification commands. See [`artifacts/README.md`](artifacts/README.md).

## Important distinction: final stack vs TWRP experiments

GENA 1.4 and TWRP were central to understanding the device and the powered-off charging failure. Several TWRP/KPOC designs were investigated and at least one Tier-A hybrid was statically validated. **The final locked stack documented here does not retain TWRP as the installed `vendor_boot`; it uses the stock-derived KPOC-compatible vendor boot.** TWRP remains historical/experimental work and must not be silently reintroduced into the final stack.
