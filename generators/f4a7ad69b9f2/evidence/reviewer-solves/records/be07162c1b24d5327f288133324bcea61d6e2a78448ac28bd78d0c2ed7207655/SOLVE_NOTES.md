# Solve work log

## Exposure

I had not opened this task's generator, rule, notes, reference solutions, private
query labels, or previous solution explanations. I used only the prepared visible
examples and small Python probes over `challenge.json`.

## Revision 1 — crop, sort, and top-align colored objects

The inputs contain three nonzero monochrome objects on a larger black canvas. The
outputs preserve every colored cell and each object's orientation, crop away the
surrounding canvas, place the crops at the top, and put one black column between
adjacent crops.

A probe extracted each color's bounding box, dimensions, binary mask, cell count,
and the output's left-to-right color order. Across all five demonstrations, the
order is exactly increasing bounding-box width and then increasing height:

- example 0: `(2×3), (4×2), (4×4)`
- example 1: `(2×2), (3×2), (3×3)`
- examples 2–3: `(2×2), (4×3), (4×3)`
- example 4: `(3×3), (3×3), (4×2)`

For equal width and height, examples 2 and 3 order the normalized binary masks
lexicographically. Example 4 has two identical masks and places color 1 before
color 7, so I use color number as the final visible tie-break. This composite key
`(width, height, binary-mask, color)` reproduces all demonstrated orders. I
considered count/area ordering, original scan order, left-to-right position, and
vertical position; each contradicts at least one demonstration.

Before implementation, I ran a visible-example assertion harness against the
provided stub and observed the expected `NotImplementedError` failure. The first
implementation extracts one crop per nonzero color, sorts with the key above,
and top-aligns the crops with one blank separator column.

Remaining uncertainty: the examples do not prove that numerical color is the
intended tie-break for identical shapes. It is the only observable discriminator
in the one demonstrated exact-shape tie and therefore the least-assumptive choice.
