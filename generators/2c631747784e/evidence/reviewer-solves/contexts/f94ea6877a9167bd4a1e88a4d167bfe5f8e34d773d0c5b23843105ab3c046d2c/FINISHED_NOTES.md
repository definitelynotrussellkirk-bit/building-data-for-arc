# Solve work log

## Prior exposure

Before this solve phase I had already inspected the selected generator and canonical Racket while repairing the assigned source, so earlier rule exposure is **yes**. After `solve prepare`, I did not reopen the generator, Racket, reference solutions, private labels, or prior solution explanations. The implementation below was derived only from the visible `challenge.json` examples.

## Revision 1

**Observation.** In every visible pair, color 8 is unchanged background. All non-8 cells keep their coordinates and counts. They form one orthogonally connected, non-branching path. Reading colors from either endpoint in the input, the output puts the same sequence back in reverse order. Example 0 changes endpoint-to-endpoint sequence `2,9,1,7,2,9,5,6` to `6,5,9,2,7,1,9,2`; the other examples have the same property even when colors repeat.

**Hypothesis.** Find the two degree-1 cells among all non-8 cells, walk the unique 4-neighbor path, reverse the collected colors, and repaint the same coordinates. Endpoint choice is immaterial because reversing a sequence and simultaneously choosing the opposite traversal produces the same coordinate-to-color mapping.

**Implementation.** `solution.py` copies the grid, handles empty and one-cell cases, validates rectangularity, traces the path without using row-major order, rejects disconnected or branching shapes, and reverses only the path colors.

**Alternatives rejected.** Row-major reversal does not fit bends in examples 0 and 2. Sorting colors does not preserve the observed endpoint sequence. Swapping only endpoints cannot explain the interior changes. Geometry movement is unnecessary because every foreground coordinate remains occupied.

**Remaining uncertainty before check.** None material for the visible distribution; the only structural assumption is that each episode contains one simple non-8 path, which all three examples demonstrate.
