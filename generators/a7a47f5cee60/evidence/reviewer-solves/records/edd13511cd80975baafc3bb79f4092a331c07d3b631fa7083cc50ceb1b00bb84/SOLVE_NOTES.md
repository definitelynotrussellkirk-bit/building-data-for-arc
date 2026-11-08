# Solve work log

## Prior exposure

I had already inspected this task's generator and Racket authority during the assigned repair, so this is an exposed post-repair solve, not a blind solve. During this solve episode I did not reopen the generator, Racket rule, private query labels, reference solutions, or earlier solution explanations; I used only the visible prepared examples.

## Revision 1 — component-contact articulation hypothesis

All visible outputs preserve the input dimensions, erase everything to black, and recolor exactly one entire monochromatic region cyan (8). The selected region is not identified by a fixed input color or size: train 0 selects the 2x2 color-6 region, train 1 selects the two-cell color-5 region, and train 2 selects the 2x2 color-5 region.

Treating each monochromatic four-connected nonzero region as a vertex and cardinal touching between differently colored regions as an edge explains all three. The selected vertex is an articulation point: removing it increases the number of connected components in the region-contact graph. Disconnected 2x2 blocks elsewhere remain ordinary distractors and must be included in the baseline component count rather than ignored.

I implemented an independent flood fill, contact graph, and remove-one-vertex component-count test. The output is a same-size zero grid with every articulation region painted 8. Main alternatives rejected by the examples are fixed color, largest region, and maximum degree alone; the second example contains a denser core where graph disconnection is the distinguishing property.
