#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 ORIGINAL_PACKET.zip RETURN_ARCHIVE.zip EMPTY_DESTINATION" >&2
  exit 2
}

[[ $# -eq 3 ]] || usage
original=$(realpath "$1")
returned=$(realpath "$2")
destination=$3

[[ -f "$original" ]] || { echo "missing original packet: $original" >&2; exit 2; }
[[ -f "$returned" ]] || { echo "missing return archive: $returned" >&2; exit 2; }
[[ ! -e "$destination" ]] || { echo "destination already exists: $destination" >&2; exit 2; }

mkdir -p "$destination"
destination=$(realpath "$destination")
unzip -q "$original" -d "$destination"
unzip -p "$returned" patches/source.patch > "$destination/source.patch"

printf 'original_zip=%s\nreturn_archive=%s\ndestination=%s\n' \
  "$original" "$returned" "$destination"
printf 'patch_sha256=%s\n\n' "$(sha256sum "$destination/source.patch" | awk '{print $1}')"

echo '=== patch paths ==='
grep '^diff --git' "$destination/source.patch"

echo
echo '=== apply check ==='
cd "$destination/WORK"
git init -q
git apply --check "$destination/source.patch"
echo 'git apply --check: PASS'
git apply "$destination/source.patch"
echo 'git apply: PASS'

echo
echo '=== selected generator hash ==='
sha256sum repo/generators/2aa2f3b2ed8f/generator.py

python_bin=${PYTHON_BIN:-}
if [[ -z "$python_bin" ]]; then
  if [[ -x /opt/pyvenv/bin/python3 ]]; then python_bin=/opt/pyvenv/bin/python3; else python_bin=python3; fi
fi

echo
echo '=== focused portable tests ==='
cd repo
PYTHONPATH=shared/runtime:src "$python_bin" -m pytest \
  --import-mode=importlib generators/2aa2f3b2ed8f/tests -q
