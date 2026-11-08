# Solve work log

I had not opened this task's generator, Racket rule, canonical record, reference
solution, private query labels, or prior solution notes. I also had not opened the
assigned repair generator before completing this solve.

## Revision 1 — centered legend stencils

**Hypothesis.** The first all-9 row separates a legend from a drawing area. In
the legend, all-9 columns split the rows above the divider into equal stencil
blocks. Each block contains one nonzero color. A singleton of that color below
the divider marks the center cell of a copy of the corresponding stencil.

**Evidence from the visible examples.** In train 0, the color-5 legend block is
a 2×2 square occupying the upper-right of its 3×3 block. Centering it on the
color-5 singleton at `(5,1)` produces output cells `(4,1)`, `(4,2)`, `(5,1)`,
and `(5,2)` exactly. The color-7 block centered at `(8,1)` likewise produces
the two output rows at rows 8–9. The same offsets explain every singleton in
trains 1 and 2, including several colors and repeated anchors.

**Alternatives rejected.** Treating a singleton as the stencil's upper-left
corner fails train 0 immediately. Aligning by the stencil's colored bounding box
also fails because the surrounding 3×3 block, not the cropped shape, determines
the offsets. Iteratively expanding newly painted cells would overproduce; only
the original lower-region singleton cells are anchors.

**Implementation.** Find the first all-9 divider row; find all-9 separator
columns above it; parse each intervening block; store colored offsets relative
to the block center; snapshot all matching cells below the divider; stamp each
shape onto a copy of the grid, clipping only at the outer boundary.

**Probe.** A local test loaded all three visible train pairs from
`challenge.json`. Before implementation it failed at the supplied
`NotImplementedError`; after implementation all three exact-grid comparisons
passed. Remaining uncertainty is limited to unseen malformed layouts (for
example, a legend block containing multiple colors), which the visible data do
not support.
