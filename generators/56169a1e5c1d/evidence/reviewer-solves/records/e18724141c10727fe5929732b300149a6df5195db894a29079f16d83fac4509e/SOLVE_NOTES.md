# Solve work log

## Information boundary

Before this post-repair solve I had already inspected and repaired the assigned
Python generator and therefore had earlier exposure to the intended rule.  For
this solve episode I closed those sources and used only `solve/challenge.json`,
the starter files, my own code, and the checker feedback.  I did not consult the
Racket rule, generator implementation, private query labels, or any reference
solution while solving.

## Revision 1

**Visible-example observations.**  Every changed cell is the center of a 3x3
square whose two opposite diagonal corners already contain the same nonzero
color:

- training 1 adds color 6 between `(0,2)` and `(2,0)`, and color 2 between
  `(4,3)` and `(6,5)`;
- training 2 adds color 3 between `(5,6)` and `(7,8)`, and color 9 between
  `(7,5)` and `(9,3)`;
- training 3 adds color 5 between `(5,2)` and `(7,4)`, and color 3 between
  `(4,8)` and `(6,6)`.

Axis-aligned equal colors, unequal-color diagonal corners, pairs at another
distance, and a diagonal pair whose midpoint is already occupied remain
unchanged.  That makes the visible rule: from the original input, find every
same-color endpoint pair separated by exactly two rows and two columns; copy
that color into its blank midpoint.

**Implementation.**  Group original nonzero cells by color, examine unordered
pairs, collect blank midpoint additions for `abs(dr) == abs(dc) == 2`, and
apply all additions only after scanning.  Delaying writes prevents an inserted
cell from becoming a new endpoint during the same solve.

**Predicted queries before checking.**

- query 1: add color 4 at `(5,4)` and color 7 at `(5,5)`;
- query 2: add color 4 at `(1,6)`, color 1 at `(3,6)`, and color 7 at `(7,4)`.
  The color-3 pair around `(5,2)` is deliberately blocked by the existing 5.

**Alternatives rejected from the examples.**  Completing any diagonal line,
using any same-color pair regardless of distance, reacting to horizontal or
vertical pairs, overwriting occupied midpoints, and recursively using newly
inserted cells all contradict visible counterexamples or add behavior not
supported by the examples.

**Remaining uncertainty before feedback.**  The examples do not show two
colors proposing different values for the same blank midpoint.  The solver
collects a value only when proposals agree; generated instances appear designed
to avoid such conflicts.
