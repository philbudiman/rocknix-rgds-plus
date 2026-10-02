#!/bin/bash
# SPDX-License-Identifier: GPL-2.0
set -euo pipefail
shopt -s nullglob
images=(target/*-Specific.img.gz)
flags=()
tag="rocknix-baseos-${GITHUB_RUN_NUMBER}-${GITHUB_RUN_ID}"
if [ "${SMOKE_TEST}" = true ]; then
  images=(target/SMOKE-TEST-DO-NOT-FLASH.img.gz)
  tag="baseos-smoke-${GITHUB_RUN_ID}"
  flags+=(--draft)
  printf 'Publishing test only. Dummy image: DO NOT FLASH.\n' > release-notes.md
else
  cat > release-notes.md <<EOF
RG DS Plus BaseOS from ${GITHUB_SHA}.
Stock BL31 suspend configuration and rails: ${SUSPEND}.
Flash the Specific image to TF1. Put ROMs in roms/nds/ on FAT32/exFAT TF2.
Reports: roms/baseos-logs/. Hardware bring-up remains unconfirmed.
Test instructions: https://github.com/${GITHUB_REPOSITORY}/blob/${GITHUB_SHA}/rocknix/README.md
EOF
fi
[ "${#images[@]}" -eq 1 ] || { echo "Expected exactly one Specific/dummy image" >&2; exit 1; }
image=${images[0]}
[ -s "$image" ] && [ -s "$image.sha256" ]
(cd target && sha256sum --check "${image#target/}.sha256")
gh release create "$tag" "${flags[@]}" --repo "$GITHUB_REPOSITORY" --target "$GITHUB_SHA" \
  --prerelease --latest=false --title "RG DS Plus BaseOS — $tag" \
  --notes-file release-notes.md "$image" "$image.sha256"
