# Solve work log

## Provenance

I had already inspected the selected generator and canonical rule during the
repair phase, so this is **not blind**; I will record earlier exposure as `yes`.
For this solve phase I used only the visible examples printed by `solve prepare`
and did not reopen the generator, Racket rule, reference solutions, private
labels, or prior solve explanations.

## Revision 1

Visible pattern: every input contains two solid color-4 rectangles. The output
preserves each border and recolors only strict interior cells. The smaller-area
rectangle receives color 1; the larger-area rectangle receives color 2. This
explains all four demonstrations, including examples where the smaller object is
later in row-major order, so position is not the ranking key.

Implementation: find 4-connected color-4 components, compute each bounding box
and area, sort by increasing area, then recolor bbox interiors with 1 and 2.
The original grid shape and all border/background cells are retained.

Remaining uncertainty before checking: the visible examples all contain exactly
two solid rectangles with distinct areas. Equal-area or nonrectangular behavior
is not inferable, but neither appears in the visible challenge.
