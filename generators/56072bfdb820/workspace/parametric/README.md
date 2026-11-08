# Boundary-mode parametric prototype

This task-local prototype leaves the production generator and canonical
`RULE_HASH` unchanged. It declares one bounded episode-level parameter:

- `boundary_mode="clip"` (default): exact canonical behavior.
- `boundary_mode="wrap"`: proposed color-5/color-8 diamonds that leave the 3x3
  meta-grid wrap modulo 3 instead of being discarded.

The parameter is selected once per episode. All demonstrations and the hidden
query use that same setting, and every generated demonstration distinguishes
it from the other declared setting. `public_challenge()` strips the parameter,
program, pair indices, and query outputs.

Run focused tests from the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/56072bfdb820/tests/test_parametric_prototype.py
```

Materialize source-bound Racket evidence (after `build_evidence.py` is present):

```bash
python3 review.py run python3 \
  generators/56072bfdb820/workspace/parametric/build_evidence.py \
  --out ../checks/parametric
```
