# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before preparation I had already inspected
this task's generator and canonical Racket rule while reviewing it, so earlier
rule exposure is **yes**. During this solve phase I did not reopen the generator,
Racket source, reference solutions, or private query labels; I used only the
public challenge and my own Python.

## Revision 1

**Visible pattern.** The nonzero color is a fixed obstacle mask and all additions
are color 1 on cells that were zero. The examples show unions of axis-aligned
empty square regions. The largest empty square(s) are always selected; smaller
empty squares are selected only when they do not overlap the union of any global
maximum square. This explains tied largest squares, the large connected painted
regions, and the unpainted zero pockets that belong only to squares overlapping
a selected maximum.

**Implementation.** Enumerate every all-zero square of side at least 2 on the
original input. Build the union of every globally largest square. Paint that
union plus every other empty square whose full cell set is disjoint from the
largest-square union. Preserve all nonzero cells and shape.

**Test discipline.** I first wrote `test_visible_solution.py`; it failed on the
stub with `NotImplementedError`. I then implemented the rule and reran the same
four-example test before invoking the packet checker.

**Remaining uncertainty.** The visible examples determine the threshold as side
2 and the disjointness reference as the complete union of global maxima. Query
labels remain masked, so query correctness is not claimed here.
