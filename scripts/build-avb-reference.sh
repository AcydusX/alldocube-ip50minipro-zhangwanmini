#!/usr/bin/env bash
# REFERENCE ONLY. Requires the original custom private key and avbtool.
# Never commit the private key.
set -euo pipefail

: "${KEY:?set KEY to private AVB PEM path}"
: "${SYSTEM:?set SYSTEM to KPOC-GSI-ANDROID16-CANDIDATE-01.img}"
: "${VENDOR:?set VENDOR to STOCK-VENDOR-KEYMINT-HYBRID-03-NOAVB.img}"
OUT=${OUT:-./out-avb}
mkdir -p "$OUT"

cp --reflink=auto "$SYSTEM" "$OUT/system.img"
cp --reflink=auto "$VENDOR" "$OUT/vendor.img"

python3 ~/avbtool.py add_hashtree_footer \
  --image "$OUT/system.img" \
  --partition_name system \
  --partition_size $((0xC7F88000)) \
  --hash_algorithm sha256 \
  --algorithm SHA256_RSA2048 \
  --key "$KEY" \
  --do_not_generate_fec

python3 ~/avbtool.py add_hashtree_footer \
  --image "$OUT/vendor.img" \
  --partition_name vendor \
  --partition_size $((0x40ABF000)) \
  --hash_algorithm sha256 \
  --algorithm SHA256_RSA2048 \
  --key "$KEY" \
  --do_not_generate_fec

python3 ~/avbtool.py make_vbmeta_image \
  --output "$OUT/vbmeta_system.img" \
  --algorithm SHA256_RSA2048 \
  --key "$KEY" \
  --rollback_index 0 --flags 0 \
  --include_descriptors_from_image "$OUT/system.img" \
  --padding_size 4096

python3 ~/avbtool.py make_vbmeta_image \
  --output "$OUT/vbmeta_vendor.img" \
  --algorithm SHA256_RSA2048 \
  --key "$KEY" \
  --rollback_index 0 --flags 0 \
  --include_descriptors_from_image "$OUT/vendor.img" \
  --padding_size 4096

echo "Payload children built. Top vbmeta also requires stock descriptors,"
echo "custom chain descriptors, and regenerated vendor_boot descriptor."
