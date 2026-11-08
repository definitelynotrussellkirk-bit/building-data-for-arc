# Blind solve notes — 14042d4b8317

This is a human reasoning work log based only on `challenge.json`. I did not inspect
the generator, canonical rule, private labels, reference solutions, prior solves, or
other task-specific records.

## Observations

- Background is 0.
- Each nonzero colour occurs exactly three times in an input.
- For each colour, its cells occupy exactly two rows and two columns: three of the
  four corners of one axis-aligned rectangle.
- The output preserves every input cell and adds the missing fourth corner in the
  same colour.
- Training example 3 demonstrates that the operation is independent per colour:
  both the 7 rectangle and the 9 rectangle are completed.

## Hypothesis

For each nonzero colour independently, when its three cells are three corners of
an axis-aligned rectangle, fill the only absent corner with that colour. Leave all
other cells unchanged.

## Visible-example probes

- Train 1: rows {6,7}, columns {3,8}; missing `(6,3)` is added.
- Train 2: rows {1,2}, columns {5,10}; missing `(1,10)` is added.
- Train 3 / colour 7: rows {3,5}, columns {1,7}; missing `(5,7)` is added.
- Train 3 / colour 9: rows {1,6}, columns {11,15}; missing `(6,15)` is added.

## Implementation choice

Use a conservative per-colour guard: exactly three cells, exactly two distinct
rows, and exactly two distinct columns. Compute the 2×2 Cartesian product and
fill its unique missing coordinate. This avoids inventing connections among
unrelated same-colour cells outside the demonstrated domain.

## Expected test outputs

- Test 1: add colour 3 at row 4, column 3 (zero-based).
- Test 2: add colour 4 at `(3,1)` and colour 5 at `(9,3)` (zero-based).
