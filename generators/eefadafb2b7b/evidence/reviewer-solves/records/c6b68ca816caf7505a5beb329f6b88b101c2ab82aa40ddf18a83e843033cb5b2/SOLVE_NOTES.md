# Solve work log

## Prior exposure

Before this visible-example solve I had already reviewed the assigned generator
and its canonical rule. This is therefore **not blind**. During the solve I did
not reopen the generator, Racket source, reference solutions, private labels, or
prior solution explanations. I used only the prepared examples and my own code.

## Revision 1 — one cyan component must contact both red-block rings

Each input contains two exact red `2×2` blocks and cyan cells. The output is a
single `8` or `0`. In positive example 0, cyan cell `(1,2)` touches the ring
around the upper-left red block and is diagonally adjacent to `(2,3)`, which
touches the ring around the lower red block. This suggested that diagonal
adjacency counts. Positive example 2 also has one diagonally/orthogonally linked
cyan component reaching both blocks.

The negative examples contain cyan near both blocks, so merely asking whether
each block has some neighboring cyan is insufficient. Their contacts belong to
different cyan components. I therefore implemented:

1. locate the two red `2×2` windows;
2. form cyan components with all eight neighboring directions;
3. define a block's ring as the surrounding `4×4` box minus the red `2×2`;
4. return `[[8]]` iff one component has at least one cell in each ring,
   otherwise `[[0]]`.

A four-connected version is contradicted by example 0's diagonal link. A
component-bounding-box overlap test is also too weak because actual component
cells, not filled bounding boxes, must touch both rings.
