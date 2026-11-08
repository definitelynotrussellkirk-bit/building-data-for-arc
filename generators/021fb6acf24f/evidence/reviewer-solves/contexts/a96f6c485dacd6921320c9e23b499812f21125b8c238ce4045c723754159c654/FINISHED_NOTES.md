# Visible-only solve notes

## Prior exposure

I had already reviewed this task's generator and authority before this separately recorded solve, so this is **not blind**. During the solve episode itself I used only the visible examples in `README.md`; I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution notes.

## Hypothesis

Each nonzero color appears twice. The two cells define opposite corners of an axis-aligned bounding rectangle. Fill the background cells of that rectangle with the same color.

The two-color examples expose the overlap rule:

- In example 1, color 9 is encountered first in row-major scan order, but overlapping cells belong to color 8 in the output.
- In example 2, overlapping cells belong to color 4 rather than color 5.

Those examples support processing colors in ascending numeric order. Each color fills only cells that are still 0, so a lower color keeps contested cells and original nonzero anchors are never overwritten.

## Implementation

1. Copy the input.
2. Collect distinct nonzero colors and sort ascending.
3. For each color, find the min/max anchor row and column.
4. Fill only currently-zero output cells in the inclusive rectangle.

This also handles the one-color examples and both visible queries without a special case.
