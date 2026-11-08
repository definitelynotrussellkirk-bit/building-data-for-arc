# Solve notes — 040bfb038c65

## Exposure

This is the required post-repair visible-example solve. I had already inspected and
worked on the generator and canonical rule before preparation, so this is **not** a
blind solve. During this solve episode I did not reopen the generator, Racket rule,
reference outputs, or private labels.

## Visible-example observations

- Every input contains three or four separated yellow(4) 4-connected objects.
- The output changes exactly one whole yellow object to cyan(8).
- Train 0 rules out “largest object”: the changed object has 3 cells while the
  three unchanged objects have 4 cells.
- Train 1 rules out size alone: all four objects have 3 cells, but the changed
  straight triomino differs from the three L-triominoes.
- Train 2 includes a 5-cell changed object and two 4-cell unchanged objects, so
  the changed object can also be larger.
- The repeated objects may be rotated or reflected versions of one another.

## Hypothesis

Normalize each yellow component under all eight rotations/reflections. Exactly one
D4-canonical shape class occurs once; recolor that component from 4 to 8.

## Implementation

Extract 4-connected yellow components, compute the lexicographically smallest
normalized coordinate tuple across the eight dihedral transforms, count those
signatures, and recolor the sole singleton class. The input is returned unchanged
only as a defensive fallback if the visible invariant is absent.

No failed revision was manufactured: the first implementation directly follows the
three visible counterexamples and is the only solve revision attempted.
