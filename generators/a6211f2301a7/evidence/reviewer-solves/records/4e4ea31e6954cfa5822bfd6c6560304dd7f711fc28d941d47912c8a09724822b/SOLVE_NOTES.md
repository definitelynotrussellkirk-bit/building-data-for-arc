# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before `prepare` I had read and repaired
the selected generator and had seen the canonical transformation. During this
solve I kept the generator, Racket source, reference solutions, private query
labels, and prior solution explanations closed and used only `challenge.json`.

## Revision 1 — crop then turn right

The visible examples all discard the surrounding zero canvas. In training pair
1, the tight nonzero box is
`[[3,0,0],[2,0,1]]`; rotating that rectangle 90 degrees clockwise gives
`[[2,3],[0,0],[1,0]]`, exactly the visible output. Pair 2 supplies a tall 4x2
box and becomes the shown 2x4 output, so the transformation is not merely
"make the shape portrait." Pair 3 independently preserves all internal zeros
and colors under the same clockwise rotation.

I implemented: locate every nonzero cell, take their inclusive bounding box,
and rotate that cropped rectangle clockwise. The empty-grid branch returns an
empty grid defensively, although every visible case contains foreground.

Alternatives rejected from the visible data: transposition alone has the wrong
row order; counterclockwise rotation has the wrong color order; reflecting after
cropping fails pair 1; and rotating the entire canvas would retain padding that
all outputs omit.
