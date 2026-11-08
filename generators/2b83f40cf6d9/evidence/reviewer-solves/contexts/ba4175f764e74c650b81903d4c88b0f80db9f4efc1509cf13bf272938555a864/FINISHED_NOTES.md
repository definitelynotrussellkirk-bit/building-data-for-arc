# Solve work log

## Exposure declaration

I had seen the task's governing rule earlier in the review workflow, before this
fresh solve episode. I did **not** consult the Racket rule, generator source,
reference solutions, private query labels, or prior solution notes while writing
this solution. The inference below was checked only against the visible examples
in `challenge.json` / `README.md`.

## Visible-example inference

Each nonzero color occurs at two marker cells. For each color, the output keeps
both markers and paints a path from the first marker encountered in row-major
order to the second. A path cycle first moves one row toward the destination and
then one column toward it. This creates a one-cell-wide diagonal staircase while
both coordinates differ, followed by a straight segment after one coordinate has
matched.

Evidence from the demonstrations:

- Train 0 shows three diagonal staircases. For color 3, the first marker at
  `(1,8)` reaches `(4,9)` by row steps with the available column step interleaved,
  then continues vertically. The other colors show both leftward and rightward
  motion.
- Train 1 is especially diagnostic. Color 1 has markers in the same column at
  `(9,0)` and `(17,0)`, and every intervening cell is filled, so aligned pairs
  are not ignored. Color 4 shows a diagonal staircase from `(7,2)` to `(11,7)`.
- Train 2 covers long paths and both signs of horizontal motion. Color 4 reaches
  `(2,0)` from `(1,13)` by a row move followed by a long horizontal remainder;
  color 7 has a mostly vertical path; color 2 has a long diagonal staircase.

## Implementation and alternatives

The implementation copies the grid, discovers nonzero colors in row-major order,
and operates only on colors with exactly two occurrences. For each pair it paints
the row-then-column walk described above. I retained row-major ordering even
though the visible paths do not overlap, because it is the only demonstrated
ordering and avoids inventing a color-sorted convention.

Alternatives rejected from the visible examples:

- Draw a direct Euclidean/Bresenham line: the outputs use a specific alternating
  orthogonal staircase, not a single-pixel geometric line.
- Move column before row: Train 0 and Train 2 distinguish the corner ordering.
- Connect only diagonal pairs: Train 1's vertical color-1 segment directly
  refutes this shortcut.
- Draw a rectangle, L-shape, or shortest path with arbitrary tie-breaking: the
  exact intermediate cells consistently follow row then column on every cycle.

Remaining uncertainty is limited to inputs outside the demonstrated domain, such
as a color occurring other than twice or overlapping paths. The solver leaves
non-pair colors unchanged and deterministically applies pairs in first-appearance
order; neither contingency occurs in the visible examples.
