# Final AVB chain construction and verification

## Final system AVB image

```text
system_a.img
size 3354951680
SHA256 9777805e7815618b314f048fc2ea199e8f0acbb907dd1a96c3d7e0cfefad2941
```

Descriptor:

```text
Partition Name system
Image Size 3301928960
Tree Offset 3301928960
Tree Size 26005504
Data/Hash block 4096
FEC roots 0
Hash sha256
Root ae655bf10df2fafe8819325e5ba172da37e8bacde867926345fa58718c5b5e36
```

The entire original Android 16 KPOC payload region compared byte-for-byte identical after the AVB tail was added.

## Final vendor AVB image

```text
vendor_a.img
size 1085009920
SHA256 877c0748ccce4be7be58d4c14aec5b199945c4c5b770fc569a6134e9d411149b
```

Descriptor:

```text
Partition Name vendor
Image Size 1067798528
Tree Offset 1067798528
Tree Size 8413184
FEC roots 0
Hash sha256
Root d336d3a125eccbfafd209dd7ec11a8e0b6a775b58851a4a88cfd0e05a691a0ef
```

## Clean vbmeta_system

Final child contains exactly one system hashtree descriptor.

```text
size 4096
SHA256 2ebdc1347bd33876052d247285dba951130bc1f83f4e3963b44965505ad8a99a
key sha1 86e98d4cc425d7a56ea1933ac5d40e4f9978586a
```

The stock product descriptor was removed only after runtime proved:

```text
/product -> /system/product
```

and no separate `/product` mount existed.

## vbmeta_vendor

```text
size 4096
SHA256 1eb4c94bd76ab7e82162f2275a287298c211d6e9ac1a33a8cfdba0903209120e
key sha1 86e98d4cc425d7a56ea1933ac5d40e4f9978586a
```

## vendor_boot direct hash

Modified KPOC vendor_boot structural size:

```text
0x170B000 = 24162304
```

Descriptor:

```text
salt 738ceb3f2490f74f773d1a26a76463e0c7e6fa31f48a513bf94ea174916addc8
digest b985daa0ba256af9446d611c5d6acef9d8625bc72a557d9035d4535053576a4a
```

## Top custom vbmeta

```text
size 8192
SHA256 04d561a8bff4515d321e8bb83d214f410adf4ec0857aa3c36faea1380a64f64c
key SHA1 86e98d4cc425d7a56ea1933ac5d40e4f9978586a
```

Final graph:

```text
boot             rollback 3 -> stock key 9d808b0995768d0677fccb1efcddb7cf9e153d99
vbmeta_system    rollback 2 -> custom key 86e98d4cc425d7a56ea1933ac5d40e4f9978586a
vbmeta_vendor    rollback 4 -> custom key 86e98d4cc425d7a56ea1933ac5d40e4f9978586a
dtbo             stock direct hash
vendor_boot      custom KPOC direct hash
odm_dlkm         stock hashtree/FEC
vendor_dlkm      stock hashtree/FEC
```

## Offline verification result

The final top-level image verified:

- its own SHA256_RSA2048 signature,
- boot chain binding,
- vbmeta_system chain binding,
- vbmeta_vendor chain binding,
- dtbo direct hash,
- KPOC vendor_boot direct hash,
- odm_dlkm hashtree,
- vendor_dlkm hashtree.

`vbmeta_system` independently verified the Android 16 system hashtree.

`vbmeta_vendor` independently verified the Hybrid03 vendor hashtree.
