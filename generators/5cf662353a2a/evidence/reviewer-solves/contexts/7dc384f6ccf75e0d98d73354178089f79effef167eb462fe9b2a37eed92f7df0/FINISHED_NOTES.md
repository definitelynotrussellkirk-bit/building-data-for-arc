# Solve notes — 5cf662353a2a

This is a human visible-example work log. I had earlier rule exposure from the generator review, so this is not blind; during this solve episode I used only the prepared visible examples and did not reopen the generator, Racket source, canonical labels, or prior explanations.

## Hypothesis from the three demonstrations

Each input has singleton color-1 cells on the bottom row and one separated monochrome object per marker. The output clears the original object locations, preserves the marker row, and moves the objects above the markers.

The assignment is not by color or original position. In each demonstration the left-to-right output order follows increasing object cell count:

- example 0: color 6 has 3 cells, color 5 has 4, color 7 has 5;
- example 1: color 5 has 3, color 4 has 4, color 3 has 5;
- example 2: color 4 has 3, color 5 has 4, color 3 has 5.

Each object's normalized shape is preserved. Its leftmost bounding-box column is aligned with the assigned marker column, and its bottom bounding-box row is placed immediately above the marker row.

## Implementation plan

1. Find same-color 4-connected components, excluding background 0 and markers 1.
2. Sort components by cell count ascending.
3. Clear the grid, restore bottom-row marker cells, normalize each component to its top-left corner, and place it over the corresponding left-to-right marker, bottom-aligned one row above the marker row.
4. Return the same canvas dimensions.

The visible examples have distinct component sizes, so no tie rule is needed for these queries. The query objects also have distinct sizes (2/3/4/5 and 3/4/5).
