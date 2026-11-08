# Solve notes

## Visible-example hypothesis

The first cell of row 0 is a transform code. The remaining nonzero cells of row 0, read left to right, are an ordered color legend; zero cells only space the legend. Row 1 is a separator. In rows 2 onward, each legend color forms one isolated 4-connected object.

For each legend color, crop its object to its bounding box, apply the same transform, and concatenate the transformed crops in legend order. The crops are top-aligned with one zero column between adjacent crops.

The visible examples establish code 1 as identity, code 2 as a clockwise quarter-turn, and code 4 as a left-right reflection. Code 3 does not occur in the visible training examples; I use the remaining half-turn mapping, consistent with earlier exposure to this task family. No Racket rule or private answer was consulted after this solve episode was prepared.

## Implementation

The solver finds body objects by 4-connected nonzero flood fill, preserves any zero holes inside a crop, orders objects by legend color rather than body position, applies the shared transform, and packs the resulting rectangles into the gallery.
