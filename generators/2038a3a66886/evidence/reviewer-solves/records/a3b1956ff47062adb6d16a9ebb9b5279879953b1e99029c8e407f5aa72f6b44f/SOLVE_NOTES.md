# Solve work log

This is a human-authored work log based only on `challenge.json` during the solve episode. I had earlier rule exposure from reviewing this task's generator, so the final declaration is `earlier-exposure yes`; I did not consult generator code, Racket source, canonical data, private labels, or reference solutions during this episode.

## Visible-example observations

- Changes are row-local; grid dimensions and all blank rows stay fixed.
- Two equal nonzero cells in one row become the endpoints of a solid horizontal segment of that color.
- A row may contain two independent equal-color pairs. Training example 1 row 0 fills both the `3 ... 3` span and the `6 ... 6` span.
- Two different singleton colors in one row remain unchanged. Training example 1 row 1 (`2 ... 3`) and training example 3 row 0 (`4 ... 2`) are explicit negative cases.
- Therefore the operation is per color, not “fill between the outermost nonzero cells.”

## Hypothesis

For each row and each nonzero color occurring at least twice, copy that color across every column from its first occurrence through its last occurrence, inclusive. Leave colors occurring once and all cells outside those spans unchanged.

## Implementation

`solution.py` copies the grid, collects column indices by nonzero color within each row, and fills first-to-last only for groups with at least two indices. This directly covers the multi-pair teaching case and preserves mismatched-color decoys.
