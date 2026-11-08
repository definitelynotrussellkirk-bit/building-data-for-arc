# Solve work log

## Exposure declaration before solving

I had not opened task `5e0575c16ab4`'s generator, Racket rule, prior solutions,
private labels, or audit records. I used only `solve-blind/challenge.json` and
local Python execution.

## Revision 1 — global uniqueness plus a clear horizontal gap

Observed pattern:

- In the first training grid, two colors each occur exactly twice on one row and
  the output fills the zeros between their endpoints.
- Filling every same-color horizontal pair is too broad. In training grid 2,
  color 2 forms two horizontal pairs (four cells total), but neither is filled;
  the color-5 pair, whose color occurs exactly twice globally, is filled.
- In training grid 3, the two 8s share a row but another nonzero cell lies between
  them, so that span remains unchanged. The clear 6 and 7 spans are filled.
- Singletons, vertical pairs, and colors with three or more occurrences remain
  unchanged in training grid 4.

Hypothesis: for each nonzero color that occurs exactly twice in the entire grid,
if both occurrences are on the same row and every cell strictly between them is
background 0, fill the full horizontal interval with that color. Otherwise leave
the grid unchanged.

Implementation copies the grid, counts nonzero colors globally, groups positions
within each row, and fills only qualifying clear spans. I rejected a
"fill every row pair" rule because it contradicts the repeated color-2 examples,
and rejected a rule based only on uniqueness because the obstructed 8 pair must
also remain unchanged.

Remaining uncertainty: the visible examples do not show a unique horizontal pair
with a nonzero obstacle of the same color repeated elsewhere in a more complex
layout, but the conjunction of global count, row alignment, and clear interior
explains every shown change and non-change.
