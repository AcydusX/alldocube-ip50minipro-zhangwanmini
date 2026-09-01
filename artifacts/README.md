# Binary artifact policy

Firmware binaries are intentionally not committed to Git.

Reasons:

- multi-gigabyte system/vendor/super images,
- device/firmware revision specificity,
- private AVB signing key sensitivity,
- reproducibility is better expressed with hashes, sizes, and build scripts.

## Historical deployment directory

```text
E:\alldocube_logo_work\LOCKED-AVB-TEST-01
```

Expected files/hashes are in `manifests/artifacts.yaml` and `manifests/known-good-sha256.txt`.

## Private key

Never add:

```text
alldocube-avb.pem
```

to Git, issues, chat attachments, CI logs, or public releases.

If a new key is generated, it changes the LK modulus, top trust root, child-chain keys, vbmeta hashes, and runtime digest. Treat that as a new trust-root generation, not a minor rebuild.
