# Solve work log

## Exposure declaration

Before this prepared solve I had reviewed the task's generator and canonical rule as part of the assigned repair, so this is **not** an independent blind solve.  After `solve prepare` I kept the generator, Racket rule, reference solutions, private labels, and earlier solution notes closed.  Everything below was reconstructed from `challenge.json` and local probes over the visible pairs.

## Revision 0 — skeleton

The prepared `solution.py` raised `NotImplementedError`.  I added a visible-pair regression test and ran it before implementation; it failed on the first pair as expected (`checks/post-solve-tdd-red.log`).

## Visible structure and hypothesis

Across all three training pairs, every newly colored cell is a non-7 cell with exactly two orthogonal 7-neighbours.  That local test also selects a few isolated exterior pockets, but the intended cells form the unique largest 4-connected component.  Ordered from either endpoint, that component is a simple one-cell-wide channel between two orange walls.

The marker cases distinguish two contexts:

- no 9 marker: fill the whole channel with 8;
- 9 on a straight channel segment (train 1): fill the whole channel, replacing 9 with 8;
- 9 at a channel bend (train 2): split the ordered path at 9, keep the 9, and fill only the longer of the two sides.

This accounts for the apparent false local candidates because they are not connected to the main channel, and it accounts for train 2 leaving the short two-cell side blank.

## Implementation

`solution.py` constructs candidate cells, extracts the largest 4-connected component, orders its simple path from an endpoint, classifies a marker as straight versus bend from its two path neighbours, and applies the three cases above.  The only remaining uncertainty is behavior on malformed branched/cyclic candidate components or an endpoint marker; neither appears in the visible lesson, and the implementation uses deterministic conservative fallbacks.
