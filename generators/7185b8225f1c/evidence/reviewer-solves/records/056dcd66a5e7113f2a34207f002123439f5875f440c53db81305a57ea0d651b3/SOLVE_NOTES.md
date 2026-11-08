# Solve work log

## Exposure declaration before solving

I had already inspected this task's generator and canonical rule during the repair phase, so this is an exposed post-repair solve, not a blind solve. During this solve I consulted only the visible challenge presentation and my own code; I did not reopen the generator, Racket source, reference solutions, or private query labels.

## Revision 1

The visible examples show that red cells are grouped by four-neighbor connectivity. A red singleton is copied unchanged. For each component with at least two cells, take its complete axis-aligned bounding box, extend that box by one row and one column on every side (clipped to the canvas), and turn every black cell in the resulting rectangle green. Preserve all red cells. This explains the vertical domino in example 1 and, crucially, the concave L components in examples 0 and 2: the empty cell inside the component's bounding rectangle and the outer box corners are all green, so a mere per-cell halo is too narrow.

I implemented a flood fill for each red component and direct rectangle painting. The remaining uncertainty is limited to unseen edge clipping and overlapping rectangles, both handled naturally by clipping ranges and painting only zeros.
