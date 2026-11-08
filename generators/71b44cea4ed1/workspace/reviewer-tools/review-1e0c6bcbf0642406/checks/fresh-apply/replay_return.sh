#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "usage: $0 ORIGINAL_PACKET_ZIP SOURCE_PATCH FRESH_ROOT REPORT_JSON EXPECTED_GENERATOR_SHA256" >&2
  exit 2
fi

packet_zip=$(realpath "$1")
source_patch=$(realpath "$2")
fresh_root=$(realpath -m "$3")
report_json=$(realpath -m "$4")
expected_generator_sha256=$5

rm -rf "$fresh_root"
mkdir -p "$fresh_root" "$(dirname "$report_json")"
unzip -q "$packet_zip" -d "$fresh_root"

work_root="$fresh_root/WORK"
cd "$work_root"
git init -q
actual_git_root=$(git rev-parse --show-toplevel)
if [[ "$actual_git_root" != "$work_root" ]]; then
  echo "unexpected git root: $actual_git_root (expected $work_root)" >&2
  exit 3
fi

git apply --check "$source_patch"
git apply "$source_patch"

mapfile -t changed_paths < <(
  sed -nE 's#^diff --git a/([^ ]+) b/.*#\1#p' "$source_patch"
)
if [[ ${#changed_paths[@]} -eq 0 ]]; then
  echo "patch has no changed paths" >&2
  exit 4
fi

hashes_tsv=$(mktemp)
pytest_log=$(mktemp)
cleanup() { rm -f "$hashes_tsv" "$pytest_log"; }
trap cleanup EXIT
for path in "${changed_paths[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "patched path missing: $path" >&2
    exit 5
  fi
  printf '%s\t%s\n' "$(sha256sum "$path" | awk '{print $1}')" "$path" >> "$hashes_tsv"
done

generator_path="repo/generators/71b44cea4ed1/generator.py"
actual_generator_sha256=$(sha256sum "$generator_path" | awk '{print $1}')
if [[ "$actual_generator_sha256" != "$expected_generator_sha256" ]]; then
  echo "generator hash mismatch: $actual_generator_sha256 != $expected_generator_sha256" >&2
  exit 6
fi

cd repo
set +e
env PYTHONPATH=shared/runtime python3 -m pytest -q generators/71b44cea4ed1/tests/test_generator.py >"$pytest_log" 2>&1
pytest_exit=$?
set -e
cat "$pytest_log"
if [[ $pytest_exit -ne 0 ]]; then
  exit "$pytest_exit"
fi

export PACKET_ZIP="$packet_zip"
export SOURCE_PATCH="$source_patch"
export FRESH_ROOT="$fresh_root"
export WORK_ROOT="$work_root"
export REPORT_JSON="$report_json"
export EXPECTED_GENERATOR_SHA256="$expected_generator_sha256"
export ACTUAL_GENERATOR_SHA256="$actual_generator_sha256"
export HASHES_TSV="$hashes_tsv"
export PYTEST_LOG="$pytest_log"
export PYTEST_EXIT="$pytest_exit"
python3 - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

hashes = {}
for line in Path(os.environ["HASHES_TSV"]).read_text().splitlines():
    digest, path = line.split("\t", 1)
    hashes[path] = digest
pytest_output = Path(os.environ["PYTEST_LOG"]).read_text()
report = {
    "schema": "arc-review-fresh-apply-v1",
    "status": "passed",
    "packet_zip": os.environ["PACKET_ZIP"],
    "packet_zip_sha256": sha256(os.environ["PACKET_ZIP"]),
    "source_patch": os.environ["SOURCE_PATCH"],
    "source_patch_sha256": sha256(os.environ["SOURCE_PATCH"]),
    "fresh_root": os.environ["FRESH_ROOT"],
    "git_root": os.environ["WORK_ROOT"],
    "git_root_verified": True,
    "git_apply_check_exit_code": 0,
    "git_apply_exit_code": 0,
    "changed_paths": list(hashes),
    "changed_path_sha256": hashes,
    "expected_generator_sha256": os.environ["EXPECTED_GENERATOR_SHA256"],
    "actual_generator_sha256": os.environ["ACTUAL_GENERATOR_SHA256"],
    "focused_test_command": [
        "env", "PYTHONPATH=shared/runtime", "python3", "-m", "pytest", "-q",
        "generators/71b44cea4ed1/tests/test_generator.py",
    ],
    "focused_test_cwd": "repo",
    "focused_test_exit_code": int(os.environ["PYTEST_EXIT"]),
    "focused_test_output": pytest_output,
}
Path(os.environ["REPORT_JSON"]).write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
PY

printf 'fresh-apply report: %s\n' "$report_json"
