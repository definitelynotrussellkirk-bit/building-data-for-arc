# Solve work log

I had not seen this task's Racket rule, generator, reference solution, private labels,
or earlier solution notes before the blind solve.

## Revision 1 — rotate around the 9 marker

The unique color-9 cell stays fixed in all four demonstrations.  Expressing every
other colored cell as `(dr, dc)` relative to that marker, the output position is
consistently `(dc, -dr)`: a 90-degree clockwise rotation around the 9.  Colors and
the grid dimensions are preserved.

I checked this coordinate rule manually on several distinctive cells:

- Example 0: relative `(1, 2)` becomes `(2, -1)`, matching the far-right input 2
  and the lower output 2.
- Example 1: relative `(3, 2)` becomes `(2, -3)`, matching the second color-2 cell.
- Example 2: relative `(1, -3)` becomes `(-3, -1)`, matching the upper-left output 1.
- Example 3: relative `(5, 0)` becomes `(0, -5)`, matching the left output 1.

The implementation locates the unique 9, creates a zero background of the same
shape, keeps the 9 fixed, and rotates every other nonzero cell.  It rejects inputs
without exactly one 9 or whose rotated cells would leave the canvas; the visible
examples suggest the generator guarantees those preconditions.

Remaining uncertainty: no visible example has a rotated collision, multiple 9s,
or a nonzero background, so the solution treats those as outside the task domain.
