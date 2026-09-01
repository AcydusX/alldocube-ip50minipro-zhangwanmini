# Custom AVB root and custom LK build

## Key material

Historical private key path:

```text
~/alldocube-locked-avb/keys/alldocube-avb.pem
```

**Never commit this file.**

Recorded metadata:

```text
private PEM SHA256 fa4c20e4aae9ef9f7697a19a594e53f8995ce4890718e3362a88229633a759b2
AVB pubkey size 520
AVB pubkey SHA256 b6abf2642a0cda00c4d7773b9d8a709abc44e5273f43a8e9b2a589b0452de6d1
AVB pubkey SHA1   86e98d4cc425d7a56ea1933ac5d40e4f9978586a
custom modulus SHA256 d258ae705de48e1f6f257564a40b24b697fec418a4868fcc5c292faa43fa8f3a
RSA bits 2048
n0inv 0x949c3b95
```

## LK patch

Only one byte range was intentionally replaced:

```text
lk/data.bin[0xA5650:0xA5750]
```

Validation performed:

- same file size before/after payload patch
- prefix identical
- suffix identical
- custom modulus at exact target
- no diffs outside target
- 254 differing byte positions inside the 256-byte region
- repacked MediaTek image hashes/signatures passed `lk-check`
- re-unpacked embedded modulus matched custom modulus hash

Final image:

```text
ALldocube-LK-CUSTOM-AVB-01.img
size 2163920
SHA256 b1d89c6139757cbd67c25007e9f8a48fbaee57b7d15d0f5a5a74aed20bd2e542
```

## Why this changes expected boot state

A user-enrolled custom AVB key would normally correspond to YELLOW on an implementation supporting that flow. This project instead replaced LK's built-in trusted modulus. Therefore the custom root is expected to be treated as the built-in/OEM trusted root, making GREEN the expected locked verified-boot state.

The final post-lock GREEN property was not yet captured when this repository was generated.
