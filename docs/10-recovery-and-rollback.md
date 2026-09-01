# Recovery and rollback notes

## Recovery philosophy used in this project

Every high-risk step was staged while the bootloader remained unlocked first. The project avoided simultaneous changes to LK + payload + lock state wherever possible.

## SP Flash Tool

The user has SP Flash Tool recovery capability. This was treated as a last-resort path, not as justification for unsafe flashing.

## Preloader

Do not modify preloader for this project. Stock preloader hash:

```text
01fbb0509958228b9119180b027ef49e998ad8c723cdfe04637739f76689c416
```

The MediaTek signing investigation showed no need to patch preloader.

## LK fallback

During the unlocked custom-LK hardware gate:

- `lk_a` was changed to custom.
- `lk_b` was intentionally left stock.

After `lock_critical`, critical partition writes may require critical unlock again.

## Known stock baselines

```text
boot.img e9a502385e79a7be9b69663fd056e09f86ed8fa6d582a2438be7de94cd82890d
lk.img   0361e41ac22c455068f7f4c2125b35771b7c3b7f740bec47bb11bb244b64928c
vbmeta   6bbcf92f9028012c81e4248373dab329bb64ae61308237e7eaf39db24b7d77bb
vbmeta_system 982e4cfb7a534df43466073558498956b1cf7f7651c8edc7f601e920e0da03e9
vbmeta_vendor 4697c249e8e90a5999bddb63171bae78a3a77023ef4fb8915c48216567bf7b2a
```

## If the locked build stops booting

Do not issue random flashes. Establish first:

1. Can bootloader fastboot still be reached?
2. Does it report locked/unlocked?
3. Is critical state writable?
4. Which slot is active?
5. Did slot A become unbootable?
6. Is the custom VBMeta digest still expected?

If unlocking is required, expect a userdata wipe.

## Never use an old community verification-disabled vbmeta as the final locked root

Earlier unlocked GSI work used verification-disabled/community-style vbmeta images. They are not valid substitutes for the custom trusted-root chain documented in this repo.
