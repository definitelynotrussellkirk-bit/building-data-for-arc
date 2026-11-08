# Exact-cover label-policy prototype

This source-bound family preserves the canonical unique exact-cover search over
the 2×2 square and three oriented L trominoes.  One episode-private parameter
changes only the final label policy: `shape_type` is the byte-exact canonical
program (piece IDs 1–4), while `area` paints 4 for the square and 3 for every L.

The sampler constructs one connected color-8 mask with exactly one legal cover.
Inputs are matched across settings and use independent demonstration/query
streams.  It supports 2–6 demonstrations and 1–8 queries.  The fourth query is
a connected, uniquely coverable 30×30 mask spanning at least 25 rows and 25
columns with at least 70 occupied cells.  Demonstrations alone must identify the
selected label policy.

From the packet root:

```bash
python3 review.py run pytest -q generators/7bd583886bad/tests/test_parametric_label_policy.py
python3 review.py run python3 generators/7bd583886bad/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 3 --queries 4 \
  --out generators/7bd583886bad/workspace/parametric/evidence/current
```

The exporter replays selected labels through protected Racket and writes only
visible demonstrations/query inputs to hash-named public files.  Settings,
programs, and query answers remain private.  This is authoring evidence, not
acceptance or training admission.
