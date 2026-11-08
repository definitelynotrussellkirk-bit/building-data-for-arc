# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solutions, private
labels, audit records, or earlier solution notes. I used only the visible examples
in `challenge.json`/`README.md` and local Python checks.

## Observations and hypothesis

Each nonzero color occurs exactly twice. The output connects the two cells of each
color with a shortest orthogonal path. Starting at the first endpoint in row-major
order, the path takes one vertical step toward the second endpoint, then one
horizontal step toward it, repeating; once one coordinate is aligned, it continues
along the remaining coordinate. This explains the staircase shapes and the straight
tails.

Crossings reveal paint order. In train 0, the later-first-seen color 3 overwrites
color 8 at `(9, 3)`. In train 1, color 7 overwrites the earlier color 9 at `(5, 3)`.
In train 2, color 4 overwrites color 2 along their overlap. Therefore pairs are
painted in the row-major order of their first endpoints, with later paths on top.

An alternative diagonal/Bresenham interpretation was rejected because train 0's
color-8 path includes both `(4, 2)` and `(4, 3)`, and train 2's paths show explicit
orthogonal alternating steps rather than single diagonal cells.

## Implementation and probe

I copied the grid, collected the two positions for each nonzero color, sorted pairs
by their first row-major endpoint, and painted the vertical-first alternating path.
Before implementation, a local harness importing the untouched template failed at
`NotImplementedError`, establishing the red test. The same harness then compared
all three visible outputs exactly.

Remaining uncertainty is limited to unseen cases outside the demonstrated contract,
such as a color occurring other than twice. The solver leaves such colors unchanged
rather than inventing a pairing rule.
