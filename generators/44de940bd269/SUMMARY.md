# 44de940bd269

0-bg grid (h~5-8, w~9-11) with: (a) ONE FULL-HEIGHT color-5 (gray) VERTICAL AXIS at some column axis_col (chosen so reflection fits in bounds); (b) 3-5 scattered non-{0, 5} colored MARK CELLS, ~70% on the LEFT side of the axis and ~30% on the right, each placed only where its mirror cell is currently empty. Rule: for each non-zero non-5 cell at (r, c), compute mirror column mc = 2*axis_col - c. If (r, mc) is in bounds AND currently 0, PAINT (r, mc) with the same color as (r, c). The gray axis stays 5; original marks stay. Net: the gray vertical line acts as a mirror, completing the reflection of all non-axis colored cells across it.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
