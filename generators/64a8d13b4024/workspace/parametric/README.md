# Native parametric family: count bars, then choose column order

This family preserves the exact canonical `color_order` program and adds one
matched-input alternative, `count_descending`.

- **A:** count the cells of colors 1, 2, and 3.
- **Intermediate:** three `(color, count)` pairs; the alternative ranks them by
  descending count with the lower color first on ties.
- **B:** assign the resulting whole colored bars to the three output columns and
  render each bar at its measured height.

The alternative cannot choose an output-column mapping before the counts exist.
Replacing its ranked intermediate with fixed color order changes the final grid
on the first constructive demonstration.

The adapter supports 2–6 demonstrations and 1–4 prefix-stable queries. Inputs
are byte-identical across settings for the same seed and request. The four query
profiles are 14×16, 19×21, 24×27, and 30×30; distractor colors 4–9 make the large
scene substantive but are ignored by both rules. `audit_lessons.py` checks the
full supported count surface for supplied seeds and can emit one-query public
projections named only by visible-byte SHA-256.

Typical checks from the repository root:

```bash
python3 generators/64a8d13b4024/workspace/parametric/audit_lessons.py \
  --seed-count 64 --out /tmp/audit.json --public-dir /tmp/public
python3 -m pytest -q generators/64a8d13b4024/tests
```

The finite settings and nine named rivals are not a universal uniqueness claim.
Protected-Racket qualification remains the authority for all generated labels.
