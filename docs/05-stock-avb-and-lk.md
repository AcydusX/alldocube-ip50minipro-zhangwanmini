# Stock AVB chain and MediaTek LK trust validation

## Stock hashes

```text
preloader_tb8781p1_64.bin
01fbb0509958228b9119180b027ef49e998ad8c723cdfe04637739f76689c416

lk.img
0361e41ac22c455068f7f4c2125b35771b7c3b7f740bec47bb11bb244b64928c

vbmeta.img
6bbcf92f9028012c81e4248373dab329bb64ae61308237e7eaf39db24b7d77bb

vbmeta_system.img
982e4cfb7a534df43466073558498956b1cf7f7651c8edc7f601e920e0da03e9

vbmeta_vendor.img
4697c249e8e90a5999bddb63171bae78a3a77023ef4fb8915c48216567bf7b2a
```

## Stock top chain

```text
top key sha1 cdbb77177f731920bbe0a0f94f84d9038ae0617d
algorithm SHA256_RSA2048
rollback 0
flags 0

boot           rollback 3 key 9d808b0995768d0677fccb1efcddb7cf9e153d99
vbmeta_system  rollback 2 key fa41159a5d696abdef93176a07d0b0d001263f01
vbmeta_vendor  rollback 4 key 9577bc6c0772975ecce93c4d8a178662c728dadf
```

Direct/preserved descriptors included dtbo, vendor_boot, odm_dlkm, and vendor_dlkm.

## LK locked-key validation

The critical validator in unpacked `lk/data.bin` was disassembled. Behavior:

```text
*out_is_trusted = 0
compare vbmeta 256-byte RSA modulus against built-in LK modulus
if equal: *out_is_trusted = 1
otherwise remain untrusted
```

This disproved the idea that stock LK would simply display YELLOW and accept any arbitrary custom root while locked. The actual implementation requires the top modulus to match the LK built-in trusted modulus.

## OEM modulus

```text
lk/data.bin offset 0xA5650
length 0x100
SHA256 4ffc881faafb2d1af7dd40cfba4ca90464b4f5689ef7f4ec3a0fe7b741440688
```

The same bytes existed once in stock vbmeta at offset `0x1078`.

## MediaTek container-signing breakthrough

Using `mtk-lk-tools`:

- stock LK partitions passed data/header hash validation,
- certificate root key matched repo `root_pubk.pem`,
- image key matched repo `img_pubk.pem`,
- preloader certificate/signature verification also matched the tool keys.

This meant a modified LK could be repacked/re-signed with the exact test-key chain already accepted by this firmware family, without changing the preloader.

The project intentionally left preloader untouched.
