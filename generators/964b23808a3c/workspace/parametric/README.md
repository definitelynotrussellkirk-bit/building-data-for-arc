# Proposed `segment_owner` rule parameter

This is an **unapproved task-local prototype**. It leaves the selected canonical
generator, production API, and Racket authority unchanged.

`segment_owner` is selected once per episode from `{lower, upper}`:

- `lower` is the byte-exact canonical rule. For each selected column, the
  lower/current marker owns the blank interval immediately above it.
- `upper` preserves the same last-nonzero-is-5 selector, ordered markers,
  segment boundaries, marker colors, distractor behavior, and floating tail,
  but the upper/previous marker owns the blank interval immediately below it.

The parameter changes an actual reasoning step rather than input geometry or
cosmetic color choice. Every retained demonstration and query distinguishes the
chosen setting from the other setting.

From the packet extraction root, materialize Racket-backed evidence with:

```bash
python3 review.py run python3 \
  generators/964b23808a3c/workspace/parametric/prototype.py \
  --seeds 0 1 \
  --out ../checks/parametric/segment-owner-v1
```

Seeds `0` and `1` cover `lower` and `upper`, respectively. The private evidence
retains exact Racket text and hashes, source hashes, canonical replay, selected
and rival outputs, recipes, and one shared-input witness. Public episode files
retain demonstration labels but omit the hidden parameter, Racket source, rival
outputs, and query answer.

Focused contract tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/964b23808a3c/tests/test_parametric_segment_owner.py
```

Limits: this is finite evidence over two four-pair episodes and one declared
parameter rival. It does not establish unique induction against every possible
rule, does not add a production parametric API, and does not confer training or
catalog approval.
