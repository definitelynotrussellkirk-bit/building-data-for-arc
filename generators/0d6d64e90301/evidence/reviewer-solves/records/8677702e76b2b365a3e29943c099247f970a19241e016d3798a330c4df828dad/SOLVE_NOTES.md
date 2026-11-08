# Visible-only solve notes

## Evidence from the examples

All three outputs have exactly twice the input height and twice the input width:
4x4 -> 8x8, 4x5 -> 8x10, and 5x4 -> 10x8.  Color counts are all multiplied by four.  More specifically, each input value at `(r, c)` occupies the four output cells
`(2r, 2c)`, `(2r, 2c+1)`, `(2r+1, 2c)`, and `(2r+1, 2c+1)`.

The rectangular examples are important: they rule out whole-grid tiling and show that the operation is local, per cell, with no transpose or crop.  Zeros are copied exactly like nonzero colors, so the rule does not depend on foreground extraction.

## Implemented hypothesis

Perform nearest-neighbor upscaling by factor two in both axes: duplicate every element horizontally, then duplicate every expanded row vertically.  The implementation validates rectangular input and does not special-case colors or shapes.

## Exposure disclosure

I had earlier exposure to the repaired generator/rule during the review, as required by the workflow.  This replay nevertheless used only the visible examples above for the solve implementation and did not consult the Racket authority, private labels, or a reference solution after `prepare`.
