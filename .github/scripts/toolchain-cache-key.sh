#!/usr/bin/env bash
set -eo pipefail

. config/options ""
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

./scripts/pkgjson > "$tmp/packages.json"
./scripts/genbuildplan.py --with-json "$tmp/plan.json" --build "$@" < "$tmp/packages.json" > /dev/null
python3 - "$tmp" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
packages = json.loads("[" + root.joinpath("packages.json").read_text().rstrip().rstrip(",") + "]")
recipes = {}
for hierarchy in ("global", "local"):
    recipes.update({p["name"]: p for p in packages if p["hierarchy"] == hierarchy})
names = {p["name"].split(":")[0] for p in json.loads(root.joinpath("plan.json").read_text())}
pending = list(names)
while pending:
    for dependency in recipes[pending.pop()]["unpack"].split():
        name = dependency.split(":")[0]
        if name not in names:
            names.add(name)
            pending.append(name)
root.joinpath("names").write_text("\n".join(sorted(names)) + "\n")
PY

{
  # Archives contain absolute paths; compiler and installed library versions must match.
  printf '%s\n' "$ROOT" "$PROJECT" "$DEVICE" "$ARCH" "${BASEOS:-no}" "${BASE_ONLY:-false}" "${DS_ONLY:-false}" "${SUSPEND:-true}"
  dpkg-query -W -f='${Package} ${Version}\n' | LC_ALL=C sort
  sha256sum "$LOCAL_CC" "$LOCAL_CXX"
  git ls-files -z -- Dockerfile Makefile config scripts tools "distributions/$DISTRO" \
    .github/scripts/toolchain-cache-key.sh .github/workflows/build-aarch64-toolchain.yml \
    "projects/$PROJECT/options" "projects/$PROJECT/patches" "projects/$PROJECT/linux" \
    "projects/$PROJECT/devices/$DEVICE/options" "projects/$PROJECT/devices/$DEVICE/patches" \
    "projects/$PROJECT/devices/$DEVICE/linux" | xargs -0 sha256sum
  while IFS= read -r package; do
    (
      . config/options "$package"
      printf '%s ' "$package"
      calculate_stamp
    )
  done < "$tmp/names"
} | sha256sum | cut -d ' ' -f 1
