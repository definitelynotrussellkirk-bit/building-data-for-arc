# Blind solve work log

Task b9b63ae52d91. No earlier rule exposure; no generator, reference, prior solution, audit or private-label files opened.

## Initial observations
Five visible demonstrations have shapes 6x6, 12x9, 6x6, 6x6 and 10x12, respectively, with identical input/output dimensions. Zero positions remain zero. Every input 8 becomes either 2 or 5. Query inputs are 6x6 and 10x10; their output dimensions and labels are unknown.

## Hypotheses and probes
Considered orthogonal neighbor count, horizontal-vs-vertical run length, component membership, distance from a zero and participation in a 2x2 square. Hand counterexamples within example 0 rule out the simple forms: (0,3) and (0,4) have the same immediate neighborhood but different outputs, and (1,3) violates the proposed row/column run comparison. No solution revision has been submitted yet. Next probe measures contiguous runs in all four directions and compares them with the two output classes using visible examples only.

## Reflection hypothesis
The run/count feature probe produced mixed output classes for almost every feature and did not identify a useful threshold. Inspecting the red coordinates in example 0 revealed vertical pairs: row 0/5 both red at column 4, rows 1/4 both red at columns 3 and 4, rows 2/3 both red at columns 4 and 5. Hypothesis: leave zero unchanged; an 8 becomes 2 if its vertically reflected partner is also 8, otherwise 5. A visible-only Python probe matched all five demonstrations exactly.

## Revision 1
Implemented that horizontal-axis reflection comparison directly. This is the first submitted solve attempt; earlier rejected ideas were probes, not saved solver revisions. No masked query labels or dimensions have been consulted.
