# Vendor / KeyMint hybrid

## Problem space

A modern GSI can boot far enough to expose incompatibilities with the stock vendor security stack, especially KeyMint/Keymaster/TEE service expectations. The project produced stock-derived vendor hybrids rather than replacing the complete vendor partition with unrelated vendor content.

## Hybrid strategy

The useful hybrid path installed a generic KeyMint service into the stock-derived vendor and prevented a conflicting TrustKernel-specific service definition from starting during the GSI test.

Generic service definition used during hybrid work:

```rc
service vendor.keymint-default /vendor/bin/hw/android.hardware.security.keymint-service
    class early_hal
    user nobody
```

Generic KeyMint binary recorded hash:

```text
6a96ad12371a0e272a4d47610c9de85c02543067146e93846ec6048fd63a7aa7
```

Relevant SELinux labels were explicitly preserved/applied. The generic binary used `hal_keymint_default_exec` labeling.

## Historical Hybrid02

One intermediate image retained an AVB tail and was not the final image. Its history is useful for understanding the patch process but should not be flashed as the current baseline.

## Final Hybrid03 payload

Final pre-AVB vendor payload:

```text
STOCK-VENDOR-KEYMINT-HYBRID-03-NOAVB.img
size 1067798528
SHA256 e25c3bf669a5d4599de07cedaefada3b181731b7ab3c1d257c102a1b55279486
```

The `NOAVB` suffix is important: old hashtree/footer material was not trusted for the final locked chain. A new hashtree and custom-key vbmeta were generated later.

## Final AVB vendor

```text
vendor_a.img
size 1085009920
SHA256 877c0748ccce4be7be58d4c14aec5b199945c4c5b770fc569a6134e9d411149b
```

Hashtree:

```text
image size 1067798528
tree offset 1067798528
tree size 8413184
FEC roots 0
root d336d3a125eccbfafd209dd7ec11a8e0b6a775b58851a4a88cfd0e05a691a0ef
```

`avbtool verify_image` passed on this final image.
