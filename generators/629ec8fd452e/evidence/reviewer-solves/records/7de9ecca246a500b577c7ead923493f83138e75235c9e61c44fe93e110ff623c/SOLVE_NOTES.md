# Solve work log

## Exposure and evidence policy

Before this visible-only solve I had already reviewed the assigned generator and
its rule as part of the required repair, so earlier rule exposure is **yes**. I
did not reopen the generator, Racket source, reference solutions, private labels,
or prior solution explanations after `solve prepare`. The observations below use
only the displayed examples and my own Python implementation.

## Revision 1 — component topology

Across all three examples, the output keeps some nonzero objects in place and
turns every other nonzero cell to 0. Color is not the criterion: example 0 keeps
one color-1 object while deleting another color-1 object. Size is not sufficient
either: closed and leaking outlines can have comparable sizes.

The stable distinction is that each retained 4-connected same-color component
surrounds at least one blank cell. Filled rectangles are deleted. A nearly closed
outline with a gap to its bounding-box border is also deleted. An irregular
closed outline with an exterior tab is retained, so exact rectangularity is not
required.

Implementation plan:
1. Split nonzero cells into 4-connected, same-color components.
2. Inside each component's bounding box, flood-fill every position not occupied
   by that component from the bounding-box border.
3. Keep the component iff at least one non-component position cannot be reached
   from that border; that unreachable region is an enclosed hole.
4. Produce an all-zero grid of the original shape and copy only retained cells.

This should retain the closed color-5/8-style outlines in the two queries and
delete the filled blocks and visibly leaking outlines. Remaining uncertainty is
limited to unseen interactions such as one object nested inside another; no such
case appears in the visible distribution.
