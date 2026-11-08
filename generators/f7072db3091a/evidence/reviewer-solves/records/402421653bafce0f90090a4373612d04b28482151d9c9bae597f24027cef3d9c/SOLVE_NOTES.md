# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, reference outputs, prior solve notes, or private labels for task `f7072db3091a`. I used only `solve-blind/challenge.json` and local Python execution.

## Revision 1 — endpoint marking

**Observed transformation.** In every visible training pair, color `1` forms one or more disjoint horizontal or vertical line segments. The output preserves the grid and every color-`5` cell, while recoloring the two end cells of each color-`1` segment to color `7`. Interior cells remain `1`. A length-two segment has no interior, so both cells become `7`.

**Implementation hypothesis.** Find each maximal contiguous horizontal run of `1` cells and each maximal contiguous vertical run. For every run of length at least two, recolor its first and last cell to `7`; leave all other cells unchanged. Using both row and column scans also handles a possible crossing without changing non-endpoint cells.

**Alternatives considered.** A simple orthogonal-neighbor-degree test matches the shown disjoint straight segments, but could misclassify a crossing or touching segments. Maximal-run endpoints express the visible rule more directly. The examples do not establish what an isolated single `1` means, so the program leaves such a cell unchanged rather than inventing an unsupported convention.

**Predicted test outputs.** Test 1: mark the ends of the row-2 run (columns 1 and 5) and both cells of the column-6 run (rows 6 and 7). Test 2: mark columns 2 and 11 on row 0, rows 7 and 10 on column 8, and rows 7 and 11 on column 10. Preserve the color-`5` cell.

**Probe.** Run the official visible-example checker. If it passes, stop rather than manufacture a failed revision; masked-query correctness is intentionally unavailable.
