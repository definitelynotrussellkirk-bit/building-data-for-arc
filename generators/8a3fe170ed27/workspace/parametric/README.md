# Prototype: episode-level row-wave orientation

This directory is a **proposed parametric extension**, not a change to the selected
canonical generator or Racket authority. It preserves the task's original
reasoning structure and varies one rule parameter once per episode:

| `wave_orientation` | Four-row translation cycle | Status |
|---|---|---|
| `left_first` | `(0, -1, 0, +1)` | canonical default |
| `right_first` | `(0, +1, 0, -1)` | proposed mirror |

For either setting, the rule finds the last nonempty row, indexes the cycle by
row distance above that anchor, translates every occupied cell in a row by the
chosen offset, preserves holes, and clips cells that leave the canvas. Inputs are
the same lawful connected one-color rail/bar objects emitted by the selected
production sampler. The prototype uses four demonstrations and one query from
consecutive sample indices. Every generated demonstration must disagree with the
opposite orientation, so the hidden episode setting is visible in the lesson.

## Reproduce the retained evidence

From the outer extracted packet directory, after `python3 review.py setup`:

```bash
python3 review.py run python3 \
  generators/8a3fe170ed27/workspace/parametric/prototype.py \
  --seed 17 \
  --out ../checks/parametric/wave-orientation-seed17 \
  --write-public generators/8a3fe170ed27/workspace/parametric/examples
```

The command executes the exact standalone programs in `rules/left_first.rkt` and
`rules/right_first.rkt`. It verifies that the default matches all five labelled
canonical pairs, that Racket and the independent Python mirror agree for both
settings, and that all four demonstrations refute the retained opposite setting.
It writes private labelled evidence, public challenges with masked query outputs,
source hashes, rule hashes, a differing witness, and a file manifest.

Run the focused tests portably with:

```bash
python3 review.py run python3 -m pytest -q \
  generators/8a3fe170ed27/tests/test_parametric_wave_orientation.py
```

## Limits

This is bounded evidence for two settings at one retained seed. It is not a
production approval, a corpus-wide distribution study, or proof against
undeclared hypotheses. The proposed `right_first` setting remains outside the
selected canonical path. `generator.py`, the catalogue rule, `RULE_HASH`, and all
canonical labels are intentionally unchanged.
