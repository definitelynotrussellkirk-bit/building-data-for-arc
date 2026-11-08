# Causal scale-map family — proposed parametric extension

The exact canonical default, `fixed_outer`, duplicates outer rows and columns
with scale vectors `(2 1 2)`. The alternative, `target_weighted`, uses the
input's top-left color as a selector. Step A expands any row containing that
color at least twice by a factor of ten. Step B counts the same color in the
resulting intermediate, chooses the leftmost maximum column, and expands that
column to width 28. The final result is 3–30 rows by exactly 30 columns.

This is a real causal composition: row expansion can change which column wins.
The first minimum-lesson example rejects `wrong_order.rkt`, which counts columns
before Step A. The second rejects `heavy_rows_only.rkt`, which classifies the
expanded rows but then discards the one-copy light rows when choosing a column.
Those two examples also choose different columns, rejecting fixed-left/middle/
right painting. Both settings share identical inputs; 2–6 demonstrations and
1–4 prefix-stable queries are supported. The four-query bank covers final
heights 30, 21, 12 and 3, including a substantive 30×30 scene.

Run the focused checks and bounded protected-Racket probe from the packet root:

```bash
python3 review.py run python3 -m pytest -q generators/ecd1058990ce/tests/test_parameters.py
python3 review.py run python3 generators/ecd1058990ce/workspace/parametric/probe.py \
  --out generators/ecd1058990ce/workspace/parametric/evidence/current/probe.json
```

The default Racket file is byte-for-byte the canonical program. These variants
remain proposed and unaccepted; authoring preflight, owner source review, native
qualification and exact-source acceptance are separate gates.
