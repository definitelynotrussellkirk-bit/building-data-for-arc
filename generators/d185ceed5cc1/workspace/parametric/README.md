# Native densest-segment parametric family

This directory now contains the native promotion candidate for `d185ceed5cc1`.
The prior isolated `gravity.py` experiment is retained only as historical
prototype material and is not referenced by `promotion.json`.

The episode-fixed parameter is `packing_rule`:

- `all_right`: the exact selected canonical Racket program, byte-for-byte.
- `densest_left`: split every row at color-8 walls, count the ordered nonzero
  pebbles in each maximal segment, select the unique count-argmax segment, pack
  that segment left, and pack all other segments right while preserving order.

The task-local curriculum supports 2–6 demonstrations and 1–4 independent,
prefix-stable queries. Inputs are matched across settings. The four-query
schedule ends with a dense 30×30 case whose nonzero content reaches all four
boundaries. Every generated row has a unique count winner and a strictly wider
non-winning distractor, so a widest-segment intermediate is visibly wrong.

`audit.py` is reusable. It checks the selected programs and nine executable
shortcut competitors using demonstrations only, and emits a protected-Racket
wrong-intermediate causal witness. Python labels are deterministic claims;
qualification re-executes all labels through protected Racket.

Typical packet commands from the outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/d185ceed5cc1/tests/test_parametric_densest.py
python3 review.py run python3 \
  generators/d185ceed5cc1/workspace/parametric/audit.py \
  --seed 0 --seed 17 --demos 2 --demos 3 --demos 6 \
  --out ../checks/d185ceed5cc1/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify d185ceed5cc1 \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/d185ceed5cc1/qualification --summary
```

Reviewer readiness is not owner acceptance. Training admission remains false.
