# Solve notes — f4725b891d89

Earlier exposure: yes. I reviewed this task's generator before this solve phase. During this solve I used only the visible examples in `solve/README.md`; I did not open the generator, Racket source, canonical ledger, private labels, previous solve notes, or any reference solution.

## Visible-example observations

- The color-5 outer rectangle and both header bands are copied unchanged.
- Nonzero cells in row 1 label interior columns; nonzero cells in column 1 label interior rows.
- For a labeled row `r` and labeled column `c`, the output fills `(r,c)` exactly when the two labels are the same color, using that color.
- A zero row/column header behaves as “unlabeled” and causes no fill.
- Duplicate labels create a cross-product, not a one-to-one pairing. Train 0 has two top 2 labels and one left 2 label, producing two fills; it also has two top 7 labels and two left 7 labels, producing four fills. This rules out first-match-only and rank-pairing hypotheses.
- Unequal header colors leave the crossing at zero, ruling out filling all intersections.

## Implementation decision

Copy the grid, collect all nonzero/non-5 top and left header entries, then fill every equal-color row/column pair. Preserve all other cells.
