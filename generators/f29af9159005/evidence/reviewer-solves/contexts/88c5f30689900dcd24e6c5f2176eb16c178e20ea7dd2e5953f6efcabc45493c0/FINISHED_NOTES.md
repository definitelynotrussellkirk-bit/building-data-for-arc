# Solve work log

## Exposure declaration before solving

This is the packet's required blind-before-repair episode. Before preparing it I read only packet-level instructions (`WELCOME.md`, `RETURN-GUIDE.md`, `DUTIES.md`) and did not open the task's generator, Racket rule, canonical labels, prior solve explanations, notes, or audit records. I had no earlier exposure to task `f29af9159005` that I recognize.

## Revision 1 — yellow orthogonal cross through red

**Observed pattern.** Every training input contains one red cell (`2`) and several blue cells (`1`). The output keeps all non-background cells unchanged. It recolors every background zero in the red cell's entire row and entire column to yellow (`4`). Blue cells lying on the cross remain blue rather than being overwritten.

**Hypothesis.** Locate the unique red cell, copy the grid, and replace only zeros in its row or column with `4`.

**Checks against examples.** In training example 1, the blue cell immediately above the red cell stays `1` while the remainder of the red column is yellow. In training example 2, the blue cell at the bottom of the red column also stays `1`. The red cell itself stays `2` in all examples. These observations reject an unconditional row/column overwrite and support background-only painting.

**Implementation.** `solution.py` validates that exactly one red cell exists, preserves the rectangular grid, and paints only zero-valued cells in the red row and column.

**Remaining uncertainty.** The visible examples contain exactly one red cell, so behavior for zero or multiple red cells is outside the observed task. The implementation fails explicitly in that case rather than silently choosing one.

## Revision 1 result

The checker reported `2/3` visible examples correct. A direct visible-example diff showed the only mismatch in training example 1: the first implementation painted cells `(0,6)` and `(1,6)`, which are beyond the blue cell at `(2,6)` from the red center at `(3,6)`. The expected output leaves those cells background.

## Revision 2 — blue markers block each ray

**Revised hypothesis.** The red cell emits four independent orthogonal rays. Each ray paints consecutive background cells yellow and stops at the first non-background cell or the grid edge. A blue cell is preserved and occludes all cells behind it.

**Why this fits all visible examples.** It explains the two overpainted cells in example 1. Example 2's bottom blue cell terminates the downward ray at the boundary; the other directions are unobstructed. Example 3 has no marker on the red row or column, so all four rays reach the edges.

**Implementation change.** Replaced whole-row/whole-column painting with four directional scans that stop before the first nonzero cell. Added rectangularity validation.
