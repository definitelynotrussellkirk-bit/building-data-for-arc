# Solve notes — cf787ae40567

This is a human work log from the visible examples only. I had already reviewed the generator before this required exposed solve, so earlier rule exposure is **yes**. During this solve phase I did not reopen the generator, Racket rule, canonical ledger, reference solution, private labels, or prior solution explanations.

## Revision 1 hypothesis

Each nonzero input cell is a seed. Expand every seed to the five-cell orthogonal plus consisting of the seed and its four cardinal neighbors, clip cells outside the input boundary, take the set union of all expanded cells, and output a one-row bar of color 8 whose width is the union size. Seed colors identify occupied cells but otherwise do not affect the count.

Visible checks:

- Training 1: the two bottom-edge seeds contribute 4 and 3 clipped cells, with no overlap, giving 7.
- Training 3: two separated interior seeds contribute 5 each, giving 10.
- Training 4: two seeds at Manhattan distance 2 share their midpoint; `5 + 5 - 1`, plus an isolated five-cell plus, gives 14.
- Training 2: five interior pluses and one bottom-edge plus would total 29; the vertically separated pair at `(9,4)` and `(11,4)` (zero-based) shares one cell, giving 28.

The implementation constructs the union explicitly, so it handles both clipping and all multiplicities of overlap rather than relying on a seed-count shortcut.
