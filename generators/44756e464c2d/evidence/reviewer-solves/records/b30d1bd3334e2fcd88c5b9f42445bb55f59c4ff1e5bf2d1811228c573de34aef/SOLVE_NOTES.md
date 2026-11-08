# Solve work log

## Prior exposure

Before this solve I had read only the packet-wide start, duty, and repository-process files. I had not opened this task's generator, canonical rule, reference solution, private labels, notes, or audit evidence.

## Revision 1 — Cartesian intersections

**Visible pattern.** Each example places color-1 markers along the top edge and color-2 markers along the left edge. The output removes all markers and paints color 3 at every intersection of a selected row and selected column. Markers of the "wrong" color on an axis are distractors: a top-edge 2 does not select a column, and a left-edge 1 does not select a row.

**Hypothesis.** Select rows `r > 0` whose leftmost cell is 2, select columns `c > 0` whose top cell is 1, create a zero grid of the same shape, and place 3 at the Cartesian product of those row and column sets.

**Probe before implementation.** A visible-example harness imported the untouched template and attempted all training pairs. It failed with the expected `NotImplementedError`, confirming the harness exercised `solve` rather than passing vacuously.

**Implementation.** Added the direct row/column projection with no dependence on fixed dimensions or marker counts.

**Alternatives considered.** Copying the original markers into the output is contradicted by every example. Treating every nonzero edge cell as a selector is contradicted by training example 1's top-edge 2 and training example 2's left-edge 1.

**Remaining uncertainty.** The visible examples consistently use background 0, row color 2, column color 1, and fill color 3; no evidence supports generalizing those colors dynamically.
