# Solve work log

I had already read the selected generator and canonical rule while doing the
required repair, so this is an exposed post-repair solve. During this solve I did
not reopen the generator, Racket source, private labels, reference solutions, or
older solve explanations. I used only the visible examples printed by `prepare`.

## Revision 1

Each input contains one large, mostly solid, single-color rectangle. Its largest
same-color 4-connected component gives the output bounding box even where a few
cells inside or on the border use other colors. The output is exactly that box,
not the full input.

The remaining nonzero cells outside the box form isolated horizontal two-cell
legends. Reading a legend left-to-right as `(replacement, source)` explains every
change in the demonstrations. For example, train 0 has outside pairs `(2,4)`,
`(6,5)`, and `(3,9)`; all 4, 5, and 9 cells in the crop become 2, 6, and 3,
respectively. Train 1 and train 2 show the same rule with legends above, below,
and beside the rectangle.

I implemented: find the largest same-color nonzero component, crop its bounding
box, collect isolated outside nonzero runs of length two, map each right-hand
color to its left-hand color, and apply all mappings throughout the crop. The
main remaining uncertainty is whether an unseen task could contain another
outside nonzero run not intended as a legend; the visible grammar consistently
uses isolated length-two runs.
