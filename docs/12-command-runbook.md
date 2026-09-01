# Command runbook — reference only

These are reconstruction/reference commands from the successful project. Do not run them blindly on another firmware revision.

## Unlock flow used historically

The user reported having used both normal and critical unlock before this project stage:

```bat
adb reboot bootloader
fastboot flashing unlock
fastboot flashing unlock_critical
```

Both may wipe/reconfigure security state. Exact original unlock transcript was not preserved here.

## Dynamic partition inspection

```bat
adb reboot fastboot
fastboot getvar is-userspace
fastboot getvar partition-size:system_a
fastboot getvar partition-size:vendor_a
fastboot getvar partition-size:super
```

Runtime LP metadata:

```bat
adb shell "lpdump 2>/dev/null | head -120"
```

## Final logical resize used

Fastbootd only:

```bat
fastboot resize-logical-partition system_a 3354951680
fastboot resize-logical-partition vendor_a 1085009920
```

## Add system hashtree/footer

```bash
python3 ~/avbtool.py add_hashtree_footer \
  --image system-a16-kpoc-avb.img \
  --partition_name system \
  --partition_size $((0xC7F88000)) \
  --hash_algorithm sha256 \
  --algorithm SHA256_RSA2048 \
  --key "$KEY" \
  --do_not_generate_fec
```

## Add vendor hashtree/footer

```bash
python3 ~/avbtool.py add_hashtree_footer \
  --image vendor-hybrid03-avb.img \
  --partition_name vendor \
  --partition_size $((0x40ABF000)) \
  --hash_algorithm sha256 \
  --algorithm SHA256_RSA2048 \
  --key "$KEY" \
  --do_not_generate_fec
```

## Final clean vbmeta_system

```bash
python3 ~/avbtool.py make_vbmeta_image \
  --output vbmeta_system-custom-avb.img \
  --algorithm SHA256_RSA2048 \
  --key "$KEY" \
  --rollback_index 0 \
  --flags 0 \
  --include_descriptors_from_image system-a16-kpoc-avb.img \
  --padding_size 4096
```

## vbmeta_vendor

Built from the new vendor descriptor under the same custom key. See `scripts/build-avb-reference.sh`.

## Custom top chain replacements

```bash
python3 ~/avbtool.py make_vbmeta_image \
  --output custom-chain-descriptors.img \
  --algorithm NONE \
  --chain_partition "vbmeta_system:2:$PUB" \
  --chain_partition "vbmeta_vendor:4:$PUB" \
  --padding_size 4096
```

The stock top vbmeta descriptors were imported first, then the replacement chain descriptors and regenerated vendor_boot descriptor were imported later so matching partition descriptors were replaced.

## Hardware unlocked AVB test

Fastbootd:

```bat
fastboot flash system_a system_a.img
fastboot flash vendor_a vendor_a.img
```

Bootloader fastboot:

```bat
fastboot flash vbmeta_system_a vbmeta_system_a.img
fastboot flash vbmeta_vendor_a vbmeta_vendor_a.img
fastboot flash vbmeta_a vbmeta_a.img
fastboot set_active a
fastboot reboot
```

No `--disable-verity` / `--disable-verification` flags were used.

## Custom LK hardware gate

With bootloader still unlocked:

```bat
fastboot flash lk_a lk-custom-avb.img
fastboot reboot
```

`lk_b` was left stock at this stage.

## Runtime VBMeta check

```bat
adb shell getprop ro.boot.vbmeta.hash_alg
adb shell getprop ro.boot.vbmeta.size
adb shell getprop ro.boot.vbmeta.digest
```

Offline:

```bash
python3 ~/avbtool.py calculate_vbmeta_digest \
  --hash_algorithm sha256 \
  --image vbmeta.img
```

Expected project digest:

```text
2acf48aed4897c1a883345805d0ab23c23c06936a1fb23743e40c87124231898
```

## Final relock commands actually accepted

```bat
fastboot flashing lock
fastboot getvar unlocked
fastboot flashing lock_critical
fastboot reboot
```
