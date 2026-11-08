# Visible-only solve notes

The three examples are split by all-zero columns into equal-width panels. Each panel contains two disconnected components of one color; only the larger component appears in the output. The retained components keep their panel-local coordinates, are ordered largest first, and are overlaid onto one panel-sized background-8 canvas. When a later component collides, it is tried at nearby offsets in the visible order: zero, horizontal one-cell shifts, vertical one-cell shifts, diagonals, then two-cell cardinal shifts.

Implementation revision 1 follows that single rule. I did not open the Racket source, generator source, reference solutions, or private query labels during this solve. I had earlier rule exposure from the generator-review phase, so this is intentionally recorded as exposed rather than blind.
