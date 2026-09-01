# Dynamic partitions and AVB sizing

## Fastbootd layout before resize

```text
system_a       0xC4CF7000  3301928960
system_b       0x09129000   152211456
product_a      0x96C39000  2529398784
vendor_a       0x3FA55000  1067798528
vendor_dlkm_a  0x02508000    38830080
odm_dlkm_a     0x00055000      348160
super          0x240000000 9663676416
```

Most B-side dynamic partitions were size zero except `system_b`.

## LP metadata

Runtime `lpdump`:

```text
metadata version 10.2
metadata max size 65536
metadata slot count 3
header flags virtual_ab_device
main_a maximum size 9661579264
main_b maximum size 9661579264
update state none
current slot _a
```

There was ample super/group capacity.

## AVB capacity calculation

With stock-style FEC planning, the old partition sizes could only hold maximum filesystem payloads:

```text
system old partition -> max payload 3249741824
current system image -> 3301928960
deficit              -> 52187136

vendor old partition -> max payload 1050865664
current vendor image -> 1067798528
deficit              -> 16932864
```

The system deficit exactly matched the old 49.77 MiB tail consumed when the ext4 filesystem was expanded.

Exact minimum partition sizes calculated:

```text
system 3354951680 = 0xC7F88000
vendor 1085009920 = 0x40ABF000
```

Fastbootd resized both logical partitions to those sizes. Android booted normally after the resize.

## Final AVB mode

Final payloads used SHA-256 dm-verity hashtrees with `--do_not_generate_fec`. The larger logical sizes remained useful because they provided safe headroom and had already been hardware tested.
