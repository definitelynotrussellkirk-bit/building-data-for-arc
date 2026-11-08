#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 SOURCE_PACKET.zip FRESH_DIR" >&2
  exit 2
fi

SOURCE_ZIP=$(realpath "$1")
FRESH=$(realpath -m "$2")
PACKET_ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
WORK="$PACKET_ROOT/WORK"
PATCH="$WORK/checks/fresh-replay/source.patch"

rm -rf "$FRESH"
mkdir -p "$FRESH"
unzip -q "$SOURCE_ZIP" -d "$FRESH"

cd "$FRESH/WORK"
git init -q
test "$(git rev-parse --show-toplevel)" = "$FRESH/WORK"
git apply --check "$PATCH"
git apply "$PATCH"
python3 setup_racket.py

cd "$FRESH"
python3 review.py run python3 -m arcpuzzles check cf4fdf474ad5 \
  --stage task_tests --timeout 600 --phase after \
  --out ../checks/fresh-replay-task-tests

python3 - "$WORK" "$FRESH/WORK" "$PATCH" <<'PY'
from pathlib import Path
import hashlib, json, re, sys
working = Path(sys.argv[1])
fresh = Path(sys.argv[2])
patch = Path(sys.argv[3])
text = patch.read_text(encoding="utf-8")
paths = [m.group(1) for m in re.finditer(r"^diff --git a/(repo/\S+) b/\1$", text, re.M)]
rows = []
for rel in paths:
    expected = (working / rel).read_bytes()
    actual = (fresh / rel).read_bytes()
    rows.append({
        "path": rel,
        "working_sha256": hashlib.sha256(expected).hexdigest(),
        "fresh_sha256": hashlib.sha256(actual).hexdigest(),
        "match": expected == actual,
        "bytes": len(expected),
    })
record = {
    "schema": "fresh-patch-replay-v1",
    "patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
    "changed_path_count": len(rows),
    "all_changed_paths_match": all(row["match"] for row in rows),
    "final_generator_sha256": hashlib.sha256(
        (fresh / "repo/generators/cf4fdf474ad5/generator.py").read_bytes()
    ).hexdigest(),
    "expected_generator_sha256": "f577c3f69219ac465b9cb03c36352de625653e76d71f3ebff9df78d87093c286",
    "paths": rows,
    "focused_test_evidence": "fresh WORK/checks/fresh-replay-task-tests/checks/task_tests.xml",
}
print(json.dumps(record, indent=2, sort_keys=True))
if not record["all_changed_paths_match"]:
    raise SystemExit("changed path mismatch")
if record["final_generator_sha256"] != record["expected_generator_sha256"]:
    raise SystemExit("generator hash mismatch")
PY
