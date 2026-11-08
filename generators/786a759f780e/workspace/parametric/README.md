# Parametric hole-priority direction — `786a759f780e`

This family preserves the source task's complete nonzero-component extraction,
enclosed-hole analysis, secondary area/color keys, crops, and horizontal packing
while varying one episode-fixed primary ordering:

- `ascending` is the byte-exact canonical Racket rule.
- `descending` orders larger enclosed-hole counts first, then retains canonical
  increasing area and increasing first-row-major color tie-breaks.

Inputs are matched across settings with stable independent prefixes for 2–6
teaching examples and 1–4 queries.  Every component mixes colors so exact-color
component extraction is observably wrong.  The first two demonstrations expose
hole priority, area direction, color ties, input-order conflicts, and both
admitted settings against a finite shortcut set.

The fourth query is a 30×30 five-object boundary case with 90 painted cells and
0-, 1-, 2-, and 3-hole components.  Its packed output is exactly 30 columns.
The causal chain is nonzero-component extraction and hole counting → ordered
per-object records `(holes, area, key color, crop)` → setting-specific sorting
and packing.  `area_only.rkt` is retained only as a wrong-intermediate causal
counterfactual.
