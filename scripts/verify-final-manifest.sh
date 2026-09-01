#!/usr/bin/env bash
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
MANIFEST="$HERE/manifests/known-good-sha256.txt"
DIR=${1:-.}

# Filter comments/blank lines and verify only files present in DIR.
while read -r hash name; do
  [[ -z "${hash:-}" || "$hash" == \#* ]] && continue
  if [[ -f "$DIR/$name" ]]; then
    got=$(sha256sum "$DIR/$name" | awk '{print $1}')
    if [[ "$got" == "$hash" ]]; then
      echo "PASS $name"
    else
      echo "FAIL $name expected=$hash got=$got" >&2
      exit 1
    fi
  fi
done < "$MANIFEST"
