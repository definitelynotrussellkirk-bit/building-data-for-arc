# Solve work log

## Exposure declaration before solving

I had already inspected the task's generator and canonical Racket authority during the repair phase, so this is an exposed post-repair solve, not a blind solve. During this solve phase I used only the prepared visible examples and did not reopen the generator, Racket rule, reference solutions, private query labels, or earlier solution explanations.

## Revision 1 — bounding-box lattice hypothesis

The three visible examples preserve the source color-7 glyph exactly as a set of occupied cells, including holes and disconnected pieces. The source glyph's bounding-box width and height define horizontal and vertical lattice strides one cell larger than the box. Copies fill the first lattice row from the source's top-left anchor to the canvas boundary. Horizontal copy indices 2, 5, 8, ... (zero-based) are recolored 6 and continue down every later lattice row; all other copies remain color 7 and occur only in the top lattice row. Cells outside those copies become zero.

The first example makes the third/sixth-column cadence and vertical continuation clear. The second and third examples show that the complete sparse/hollow glyph is copied rather than only a connected component or a filled bounding box. I implemented this directly, clipping partial copies at the right or bottom edge just as the visible outputs do.

Remaining uncertainty before checking: none material; both test inputs have source shapes whose bounding boxes and one-cell gaps are visible, including a disconnected four-cell shape that tests whether all source cells are retained.
