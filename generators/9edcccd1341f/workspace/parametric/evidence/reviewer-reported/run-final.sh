#!/usr/bin/env bash
set -uo pipefail
ROOT=/mnt/data/arc_puzzles_review_043607_work
cd "$ROOT"
records=()
run() {
  local name=$1; shift
  printf '\n===== %s =====\n' "$name"
  printf 'cwd=%s\nargv=' "$PWD"
  printf '%q ' "$@"; printf '\n'
  "$@"
  local rc=$?
  printf 'exit_code=%s\n' "$rc"
  records+=("\"$name\":$rc")
  return "$rc"
}
overall=0
run parametric_tests python3 review.py run python3 -m pytest -q generators/9edcccd1341f/tests/test_parametric_frequency_target.py || overall=1
run repair_tests python3 review.py run python3 -m pytest -q generators/9edcccd1341f/tests/test_review_repairs.py || overall=1
run parametric_evidence python3 review.py run python3 generators/9edcccd1341f/workspace/parametric/prototype.py --seed 173 --difficulty medium --start 0 --out ../checks/parametric/frequency-target-s173 || overall=1
{
  printf '{\n  "overall_exit": %s,\n  "commands": {\n' "$overall"
  local_first=1
  for row in "${records[@]}"; do
    if [ "$local_first" -eq 0 ]; then printf ',\n'; fi
    printf '    %s' "$row"
    local_first=0
  done
  printf '\n  }\n}\n'
} > /mnt/data/arc_puzzles_review_043607_work/WORK/checks/parametric/final-run-status.json
exit "$overall"
