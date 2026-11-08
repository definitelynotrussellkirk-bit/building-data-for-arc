# Solve work log

## Exposure declaration before solving

I had already inspected this task's generator and Racket behavior during the assigned review, so earlier rule exposure is **yes**. During this solve phase I consulted only `solve/challenge.json` and my own code; I did not reopen the generator, authority, canonical ledger, reference solutions, or private labels.

## Revision 1 — sparse lattice boundaries move to nearest marker-defined edges

From the three visible pairs:

- Color 3 forms a sparse rectangular lattice: the union of complete rows and complete columns inside its bounding box.
- Color-6 cells outside that box indicate which outer side should move. The new side lies one cell inward from the nearest marker on that side.
- Multiple markers on one side use the nearest marker. This is visible in training example 1 on the right and training example 3 on the left.
- Only the old boundary row/column moves. Complete internal rows and columns keep their absolute coordinates while extending across the resized box.
- Color-6 markers stay unchanged and win if a drawn line would overlap them.

Implementation plan: recover the color-3 bounding box and its complete rows/columns, classify markers by side, compute the four target boundaries, redraw the row/column union on a zero grid, then restore markers. I used side precedence visible in the examples: top/bottom markers must be horizontally aligned with the source box; remaining markers left/right of the box define lateral sides.

Remaining uncertainty: none material in the visible domain. The solve is exposed rather than blind, so a passing visible check is implementation evidence, not independent rule-discovery evidence.
