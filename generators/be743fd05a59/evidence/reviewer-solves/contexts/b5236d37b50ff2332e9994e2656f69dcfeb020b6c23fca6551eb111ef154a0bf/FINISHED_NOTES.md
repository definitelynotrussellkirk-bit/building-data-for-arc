# Solve work log

## Exposure declaration before solving

I had not opened task `be743fd05a59`'s generator, Racket rule, reference solution,
private labels, notes, or audit evidence. I used only the visible examples printed
by `python3 review.py blind prepare` and the checker feedback.

## Revision 1 — unimplemented template (intent: solve)

Hypothesis from the visible examples: each color-9 cell casts a one-cell diagonal
mark down-left, changing the destination from 0 to 5. A mark is omitted when the
destination is outside the grid or already occupied by any nonzero cell. Evidence:

- Train 0: `(3,8)->(4,7)` and `(7,4)->(8,3)` are added; `(6,0)` points off-grid.
- Train 1: three legal empty destinations are added; `(9,5)->(10,4)` is blocked by
  the existing color-4 cell, and `(10,10)` points below the grid.
- Train 2: all five 9s have legal empty down-left destinations and all five become 5.

I first ran the checker against the supplied `NotImplementedError` template to
establish a failing execution record. It reported execution error and 0/3 visible
examples passed, as expected.

Alternatives considered and rejected: nearest-object connection, extending the
colored object's orientation, and drawing longer rays. The exact same local offset
explains every added cell, while the colored cells act only as blockers.

## Revision 2 — local down-left marker

Implemented a shape-preserving copy. Iterate over the original input (not newly
painted output), and for each 9 paint 5 at `(row+1, col-1)` only when that coordinate
exists and its original value is 0. Iterating over the original prevents newly
painted 5s from affecting later decisions. Ragged rows are handled by checking the
target row's actual length.

Remaining uncertainty: visible examples do not distinguish "empty only" from a
more specific exception for colored objects, but preserving all nonzero input cells
is the minimal rule consistent with every pair.
