# Solve work log

I had not opened the task's generator, Racket rule, canonical data, private labels,
or prior solution notes before this blind solve.

## Revision 1 — odd-by-odd rectangle center

Each visible input contains two single-color hollow rectangular outlines. Exactly
one rectangle has both an odd height and an odd width, hence a unique grid-cell
center. The output adds one cell, in the same color as that rectangle, at its
geometric center; the even-by-odd or odd-by-even rectangle is unchanged.

Observed checks:

- Example 0: the 3×5 color-1 outline gains its center; the 3×4 color-6 outline does not.
- Example 1: the 5×3 color-5 outline gains its center; the 4×3 color-7 outline does not.
- Example 2: the 3×3 color-9 outline gains its center; the 3×4 color-1 outline does not.

The implementation finds 4-connected monochrome components, verifies that a
component is exactly a rectangular border, and fills its center only when both
bounding dimensions are odd. This should place color 1 at (6, 7) in query 0 and
color 2 at (1, 6) in query 1. Remaining uncertainty: the examples do not show
multiple eligible odd-by-odd rectangles, so I apply the visible rule independently
to every eligible rectangle rather than adding an arbitrary uniqueness condition.
