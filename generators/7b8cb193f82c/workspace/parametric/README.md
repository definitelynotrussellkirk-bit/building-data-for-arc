# Proposed outer-layer color parameter (isolated prototype)

This task-local prototype keeps the canonical rectangular-frame and inward-layer
reasoning while varying one rule parameter once per episode:

- `outer_color = 2` — original/default canonical behavior; inward depths are
  `2, 3, 2, 3, ...`.
- `outer_color = 3` — proposed alternative; inward depths are
  `3, 2, 3, 2, ...`.

The input domain is unchanged. Each episode contains three demonstrations and
one masked query. One exact Racket program is selected from the episode seed and
used for every pair. The demonstrations have nonempty frame interiors, so they
refute the other allowed setting before the query needs that distinction.
Public files omit the hidden parameter, Racket source, rival predictions, and
query output. Private evidence retains them with hashes.

Run from the outer extraction directory using a fresh output path:

```bash
python3 review.py run python3 \
  generators/7b8cb193f82c/workspace/parametric/prototype.py \
  --out ../checks/parametric/outer-color-v1
```

Run the portable focused tests with:

```bash
python3 review.py run python3 -m arcpuzzles check 7b8cb193f82c \
  --stage task_tests --timeout 600 --phase after \
  --out ../checks/task-tests
```

This is a **proposed prototype**, not a production API, rule-hash update, or
approval of an alternative canonical rule.
