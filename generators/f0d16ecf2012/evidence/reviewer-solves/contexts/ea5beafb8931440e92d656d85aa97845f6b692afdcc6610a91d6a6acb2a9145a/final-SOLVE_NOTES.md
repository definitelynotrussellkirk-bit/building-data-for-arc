# Solve work log

I had earlier exposure to the task rule while reviewing the generator. For this
fresh solve I used only `challenge.json` and visible-check feedback; I did not
consult the Racket program, generator source, private labels, or prior solution
notes after preparation.

## Revision 1 — wall-only docking hypothesis

The visible pairs show color-9 lane walls remaining fixed while each colored
4-connected component translates east without rotation. Diagonally touching
same-color cells behave as separate components. My first executable hypothesis
moves every component until its next step would hit a color-9 wall, ignoring
its vacated source footprint. This is intentionally tested before adding any
special stopping rule; the third visible example contains a gapped connected
shape that should discriminate the hypotheses.

## Revision 2 — static source footprint

Revision 1 executed but matched 0/3 visible outputs. Reinspection of each
visible gapped component explains the common failure: the output stops when a
future translation would re-enter one of that same component's original cells,
even though the cell was vacated by an earlier step. For example, the first
training pair's color-8 shape shifts two columns; a third shift would place its
upper-left cell on the original upper-right cell. Other components still pass
through one another because their source cells are not included in this
component's blockers.

The revised solver therefore extracts same-color 4-connected components,
freezes color-9 walls plus each component's own original footprint as its
static occupied set, shifts the component east while destinations are either
free or occupied by its current translated cells, and paints all independently
translated components onto a wall-only output grid.
