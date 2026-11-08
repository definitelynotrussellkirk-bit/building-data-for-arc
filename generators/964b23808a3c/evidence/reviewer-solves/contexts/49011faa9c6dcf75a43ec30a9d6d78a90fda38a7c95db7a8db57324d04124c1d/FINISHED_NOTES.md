# Solve work log

## Exposure declaration

Before this exposed solve I had reviewed the task's generator and canonical
behavior while repairing it. I therefore treat this solve only as a check that
the repaired generated lesson is independently legible from its visible
examples. During this solve I did not reopen the generator, Racket authority,
reference solutions, or private query labels.

## Revision 1

**Visible evidence.** In every training pair, only columns whose lowest
nonzero marker is color 5 change. Other multi-marker columns remain exactly as
shown, including a column that contains a 5 internally but ends in another
color. In a changed column, markers are read from top to bottom. The current
marker's color fills from the row immediately after the preceding marker (or
row 0 for the first marker) through its own row. When the final 5 is above the
bottom edge, rows below it remain unchanged.

**Hypothesis.** Select each column whose last nonzero value is 5. For its
original nonzero markers `(row, color)` in increasing row order, paint the
closed interval from the previous marker row + 1 (initially 0) through `row`
with `color`. Preserve every other cell.

**Implementation.** `solution.py` copies the grid, identifies qualifying
columns from the original input, and performs exactly those interval fills. It
also rejects ragged grids rather than silently truncating them.

**Alternatives rejected from the visible examples.** Filling every column with
multiple markers fails on the distractors. Selecting any column that merely
contains 5 fails on the internal-5 distractor. Using the previous marker color
fails immediately because the cells above the first marker and between markers
carry the lower/current marker color. Extending the terminal 5 to the bottom
fails on the 13×13 floating-terminator example.

**Remaining uncertainty before checking.** None material: the three examples
separately expose target selection, current-marker ownership, distractor
preservation, and the floating boundary.
