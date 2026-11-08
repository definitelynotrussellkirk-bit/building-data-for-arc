# Solve work log

## Exposure before solving

I had not opened the generator, canonical rule, reference solution, private query labels,
or earlier solution notes for task `b47adc50b675`. I used only the public examples emitted
by `python3 review.py blind prepare` and the solve template.

## Revision 1 — translate the visible figure to the upper-left corner

Across all three training examples, the set of color-3 cells keeps exactly the same shape
and orientation. The only change is a translation: subtract the minimum occupied row and
minimum occupied column, so the figure's bounding box begins at coordinate `(0, 0)`. The
grid dimensions and cell colors remain unchanged; vacated cells become background color 0.

I checked this interpretation against each example by comparing relative coordinates. For
example 2, input offsets from bounding-box origin are `(0,1), (1,0), (1,1), (1,2)`, exactly
the output coordinates. The same test holds for examples 0 and 1. A local test was first run
against the untouched `NotImplementedError` template and failed as expected; after the
implementation it should pass.

Alternatives considered: moving only the connected component, cropping the grid, reflecting
the figure, or moving it to the nearest corner. Cropping is contradicted by unchanged output
shapes; reflection is contradicted by preserved relative coordinates; “nearest corner” is
contradicted by examples near the bottom-right that move specifically to the top-left.

Remaining uncertainty is limited to unseen conventions for a nonzero background or multiple
figures. Every visible instance has background 0 and one nonzero figure, so the implementation
uses all nonzero cells as the translated figure and preserves all their colors.
