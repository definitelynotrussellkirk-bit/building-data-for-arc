# Solve work log

## Exposure declaration before solving

I had not opened task `a0c86a1cb81e`'s generator, Racket rule, notes,
reference solutions, private query labels, or prior explanations. I used only
`solve-blind/challenge.json` and local Python inspection of those visible grids.

## Revision 1 — mark orthogonal bends

**Observation.** Every nonzero object is a 4-connected path made of color 3.
The output preserves object positions and recolors only some 3-cells to 6.
Across the three training examples, every changed cell is a path corner: it has
one horizontal 3-neighbor and one vertical 3-neighbor. Endpoints have one total
neighbor and remain 3; straight interior cells have two neighbors on the same
axis and remain 3.

**Probe.** I enumerated 4-connected components and compared changed coordinates
against each cell's four-neighbor pattern. All ten visible changes matched
`horizontal_neighbors == 1 and vertical_neighbors == 1`, and no unchanged cell
matched that predicate.

**Implementation.** Copy the grid, inspect the original grid (so recoloring does
not affect later neighbor tests), and recolor exactly those bend cells from 3 to
6.

**Alternatives considered.** Recoloring all degree-2 cells would incorrectly
change straight segments. Recoloring any cell with at least one horizontal and
one vertical neighbor would also include branch junctions if they appeared; the
visible objects are paths, so the exact one-plus-one condition states the
observed rule more narrowly.

**Remaining uncertainty.** The examples do not contain branch junctions or
closed loops. The chosen predicate follows the demonstrated path-corner rule
rather than extending it to those unseen cases.
