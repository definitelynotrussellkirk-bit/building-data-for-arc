# Solve work log

## Exposure statement before solving

I had not opened the Racket rule, generator implementation, reference solution,
private query labels, prior solve explanations, or any generator/audit material
for task `66e63986855b`.  I used only the visible examples emitted by
`python3 review.py blind prepare` and `WORK/solve-blind/challenge.json`.

## Revision 1 — mirrored-boundary interior fill

**Observed pattern.**  In every training example, all nonzero input cells lie on
the left side of a shape.  The rightmost occupied column over the whole input is
an outer tip.  Reflecting the row marker across the vertical axis halfway after
that global rightmost column creates a matching right boundary.  The output
removes both boundary cells and fills only the cells strictly between them.

When a row has more than one adjacent marker (training example 1, row 6), the
rightmost marker is the inner boundary.  Using the leftmost marker would produce
six cells instead of the observed two, so the row-wise rightmost marker is the
necessary choice.

For global rightmost column `m` and row-wise rightmost marker `x`, the reflected
boundary is `2*m + 1 - x`; fill columns `x+1` through `2*m-x` inclusive.  Rows
without markers remain blank.  Rows whose marker is at `m` have adjacent mirrored
boundaries and therefore contribute no filled cells.

**Probe.**  A visible-example regression script first imported the untouched
stub and failed with `NotImplementedError`.  After implementing the formula, the
same script checks all three public training pairs exactly.  The official blind
checker is the authoritative visible-only check.

**Alternatives considered.**  I considered thickening each marker or filling
from the leftmost marker, but both contradict training example 1's two-marker
row.  I also considered moving/centering the object, but matching rows and the
exact per-row widths show no vertical movement is needed.

**Remaining uncertainty.**  The examples use background color 0 and one
foreground color per episode.  The implementation preserves the rightmost
marker's color per row and otherwise assumes 0 is background, matching all
visible evidence.
