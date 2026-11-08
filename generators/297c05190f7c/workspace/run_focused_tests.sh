#!/usr/bin/env bash
set -euo pipefail
export TERM=${TERM:-dumb}
TASK=297c05190f7c
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)
RUNTIME=$(mktemp -d "${TMPDIR:-/tmp}/arcpuzzles-${TASK}-tests.XXXXXX")
trap 'rm -rf "$RUNTIME"' EXIT

cp -a "$ROOT/shared/runtime/." "$RUNTIME/"
mkdir -p \
  "$RUNTIME/puzzle_generators/per_puzzle/$TASK" \
  "$RUNTIME/data/canonical" \
  "$RUNTIME/scripts"
cp "$ROOT/generators/$TASK/generator.py" \
  "$RUNTIME/puzzle_generators/per_puzzle/$TASK/generator.py"
printf '' > "$RUNTIME/puzzle_generators/per_puzzle/$TASK/__init__.py"
cp "$ROOT/shared/data/canonical/puzzles.jsonl" \
  "$RUNTIME/data/canonical/puzzles.jsonl"
cp -a "$ROOT/shared/tools/." "$RUNTIME/scripts/"

cd "$ROOT"
PYTHONPATH="$RUNTIME" \
  python3 -m pytest -q "generators/$TASK/tests/test_generator_$TASK.py" "$@"
