# Post-repair visible-example solve — 6355eb114053

## Exposure declaration

This is an exposed post-repair solve. I previously read and edited this task's
generator and inspected its canonical rule during the repair. During this solve
phase I used only the new visible challenge, the preparation display, and my
own Python inspection. I did not reopen the generator, Racket rule, canonical
answers, prior explanations, or private query labels. This document is an
authored work log, not a token-level captured model trace.

## Observations

Examples 0 and 1 each have Input: 9 rows × 9 columns. Output: 9 rows × 9 columns.
Example 2 has Input: 9 rows × 11 columns. Output: 9 rows × 11 columns.
The two queries have inputs of 6 rows × 11 columns and 8 rows × 12 columns;
Output: unknown for both.

The output changes only zero centers with matching north, south, west and east
arms. Example 0 fills (7,3) and (7,6) with 1. Its center (1,1) is left empty
although three arms are 1, because the south arm is 7. Its occupied center
(1,5)=1 is preserved even though the four arms are 7.

Example 1 fills (1,4) with 9, (4,5) with 8 and (7,3) with 8. Its center (2,1)
has north/south/east arms of 8 but no west arm and stays zero. The near miss
at (7,6) has three 9 arms and an east 8 arm, so stays zero.

Example 2 fills (1,3) and (4,4) with 2. The three-arm 5 pattern centered at
(4,1), the mismatched 8/4 pattern centered at (7,6), and occupied (1,6)=8 stay
unchanged. Singletons elsewhere do not cause repairs.

## Revision 1 — solve intent

Scan interior zero cells using the original input. Fill from north only if that
color is nonzero and equal to the other three cardinal neighbors. Copy the grid
first, preserving every other cell. Border cells have no full neighborhood and
are untouched. These conditions explain both changed and unchanged examples;
there is no reason to use a fixed position or a favored color.

A rule using only an opposite pair, majority-of-three, or all four nonzero
without color equality contradicts visible near misses. Ignoring the existing
center color contradicts the occupied-center examples. I did not implement a
wrong revision merely to create a negative training record.
