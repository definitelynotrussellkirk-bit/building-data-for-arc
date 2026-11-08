# Proposed `cross_mode` parameter

This unapproved task-local prototype preserves the selected canonical generator
and the canonical `plus` rule. It chooses `cross_mode` once per episode from
`plus` (the original frame plus two-arm color-5 cross) or `horizontal` (the same
frame, precedence, center, and horizontal arm, but no vertical arm). Input
constraints are identical for both settings. Three demonstrations precede one
query, and every retained fixture distinguishes both settings.

From the outer extracted packet directory, run:

```sh
python3 review.py run python3 -m pytest -q \
  generators/0a9926d504f3/tests/test_parametric_cross_mode.py
python3 review.py run python3 \
  generators/0a9926d504f3/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/cross-mode-final
```

The evidence command executes the exact Racket program for every label, replays
the canonical default against all canonical pairs, stores private and public
episodes separately, and omits hidden parameters, rule text, and query answers
from public challenges. This is bounded authoring evidence, not production or
training approval.
