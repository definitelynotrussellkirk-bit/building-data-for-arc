#!/usr/bin/env bash
set -euo pipefail
# Run from the root of a fresh extraction of the original review packet.
response_zip=${1:?usage: bash replay.sh /path/to/review_response_*.zip}
unzip -p "$response_zip" patches/source.patch | (cd WORK && patch --batch --forward -p1)
python3 review.py setup
python3 review.py run python3 -m pytest -q \
  generators/ef02aedbac38/tests/test_parametric_selector_role.py \
  generators/ef02aedbac38/tests/test_parametric_public_names.py
python3 review.py run python3 -m arcpuzzles check ef02aedbac38 \
  --stage task_tests --timeout 600 --phase after \
  --out ../checks/replay-task-tests
