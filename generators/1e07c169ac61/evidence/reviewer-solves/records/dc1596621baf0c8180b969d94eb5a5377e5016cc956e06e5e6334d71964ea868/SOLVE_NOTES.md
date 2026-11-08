# Solve notes

The visible examples preserve the unique color-9 cell and move every other
colored cell while preserving its color and distance from 9. Example 1 is the
clearest orientation probe: cells directly below the anchor become cells
directly left of it, which is a 90-degree clockwise rotation in row/column
coordinates.

Hypothesis: use the unique 9 at `(ar, ac)` as the pivot, clear the canvas except
for that anchor, and map each nonzero non-9 cell `(r,c)` to
`(ar + (c-ac), ac - (r-ar))`. The examples with multiple colors show that this
acts on cells independently rather than on one selected component or color.
Out-of-bounds destinations are ignored defensively, though every visible source
appears selected so its destination fits.
