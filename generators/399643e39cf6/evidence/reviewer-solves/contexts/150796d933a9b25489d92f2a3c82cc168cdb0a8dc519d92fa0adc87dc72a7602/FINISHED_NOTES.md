# Solve notes

## Revision 1

Visible-only hypothesis:

1. Sort the two color-9 cells in row-major order. Their displacement is the copy vector.
2. Remove both 9 cells.
3. Find same-color 4-connected nonzero components.
4. Choose the component with the fewest cells. If sizes tie, use earlier bounding-box top row, then left column (and color only as a final deterministic tie-break).
5. Keep every original component and stamp a translated copy of only the selected component.

Evidence from the three demonstrations:

- Example 0 uses vector `(5, 3)` and duplicates the size-3 color-8 component rather than the size-6 color-7 component.
- Example 1 uses horizontal vector `(0, 4)`. Both color 7 and color 1 have size 3; the earlier color-7 component is copied. This rules out choosing by lowest color and establishes the positional tie-break.
- Example 2 uses vector `(4, -3)` from markers `(0,9)` to `(4,6)`, so marker order is spatial row-major rather than left-to-right. It copies the size-3 color-8 component rather than the size-5 color-5 component.

Predicted queries:

- Query 0: vector `(4,0)`; color 6 and color 2 tie at size 3, so earlier color 6 is copied to rows 4-5.
- Query 1: vector `(5,3)`; size-4 color 8 is copied to rows 6-7 while the size-7 color 7 remains unchanged.

I had already seen the rule during generator repair, so this is an exposed post-repair solve, not a blind solve. I did not consult the Racket source, private labels, or reference implementation during this solve episode.
