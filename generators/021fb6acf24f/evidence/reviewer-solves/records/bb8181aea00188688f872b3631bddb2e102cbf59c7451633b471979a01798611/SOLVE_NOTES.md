# Solve work log

## Exposure declaration

I had already inspected and repaired this task's generator before this required
post-repair solve, so the intended transformation was exposed earlier.  During
this solve I did **not** consult the Racket source, generator implementation,
reference solutions, private query labels, or earlier solution explanations.  I
used only the visible `challenge.json` examples and a local visible-example test.

## Visible-example inference

Each nonzero color appears at two opposite corners of an axis-aligned rectangle.
The output fills that color's inclusive bounding box.  When two boxes overlap,
the lower numeric color wins: examples 1 and 2 both place the larger color first
in row-major input order, yet the smaller color occupies every overlap cell.
Therefore row-major first occurrence is visibly refuted; ascending numeric color
order is required.  Filling only cells that remain zero preserves original
markers and gives earlier (smaller) colors precedence.

## Implementation and probe

I wrote `solve(grid)` to copy the grid, collect nonzero colors in ascending
order, compute each color's bounding box from its input cells, and fill only
currently-zero cells inside the box.  Before implementation, the local visible
regression failed on the prepared stub with `NotImplementedError`; after the
implementation it passed all three labeled examples.  The two masked queries
were left uninspected beyond their public inputs.

## Remaining uncertainty

The visible examples all use exactly two markers per color, as expected for the
inferred rectangle-corner representation.  Behavior for malformed colors with
one or more than two markers is outside the visible task contract; the bounding
box generalization is deterministic but not claimed as additional semantics.
