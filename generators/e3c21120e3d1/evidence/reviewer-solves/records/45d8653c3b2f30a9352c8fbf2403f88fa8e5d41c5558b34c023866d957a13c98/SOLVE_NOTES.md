# Solve work log

## Prior exposure

Before this solve episode I had already reviewed the selected generator and its
rule metadata, so earlier rule exposure is **yes**.  I did not reopen the
Racket rule, generator implementation, reference solutions, private labels, or
earlier solution notes during this solve.  The implementation below was checked
against the visible `challenge.json` examples only.

## Revision 1

**Visible observation.**  Every output exchanges the input dimensions.  For
all three demonstrations, an input cell at zero-based `(row, column)` appears
with the same color at output `(column, row)`, including background cells.  For
example, train 0's `7` at `(0, 2)` appears at `(2, 0)`, and its `5` at `(4, 4)`
remains at `(4, 4)`.

**Hypothesis.**  Transpose the complete rectangular matrix across its main
diagonal; do not crop, move components independently, recolor, or reflect after
transposition.

**Program.**  `solve(grid)` constructs each output row from one input column
using `zip(*grid)` and materializes fresh lists.

**Alternatives considered.**  A 90-degree rotation also swaps rectangular
shapes, but train 1 refutes it: the point at input `(2, 1)` maps to output
`(1, 2)`, whereas clockwise rotation would place it elsewhere.  Component-wise
movement is unnecessary because every background and colored coordinate obeys
the same matrix mapping.

**Uncertainty.**  None within the visible examples beyond the required note
that I had seen the rule earlier.  One exact hypothesis matches all three full
training grids, so I stopped after one revision.
