# Blind solve notes — 8b6543be4517

## Hypothesis
Each grid has exactly one solid color-8 row or column. Treat it as a reflection axis.
For every color-7 cell, add its mirror image across that axis when the mirrored
coordinate lies inside the grid. The output is the union of original and mirrored
7s. A mirrored 7 may overwrite a non-axis distractor color (seen with colors 4/6),
while non-7 cells otherwise remain unchanged.

## Evidence from visible examples
- Vertical example 1: right-side `(row 1, col 8)` mirrors to left-side col 2,
  overwriting a 6; left-side col 4 mirrors to right-side col 6.
- Horizontal example 2: lower row 8 mirrors to upper row 2; color-4 cells hit by
  those mirrors become 7. Out-of-bounds reflections are omitted.
- Vertical example 3 and horizontal example 4 confirm the same coordinate rule
  with different axis positions and uneven side extents.

## Implementation
Find the unique all-8 row or column, snapshot all original 7 coordinates, and
write each valid reflected coordinate as 7 into a copied grid.
