# Solve work log

## Exposure declaration

I had already learned the task family while reviewing the generator, so this episode is honestly marked **earlier-exposure: yes**. After `prepare`, I used only the new `solve/challenge.json` and my own Python; I did not open the generator, Racket authority, private labels, reference solutions, or the archived prior solve.

## Revision 1

Visible evidence:

- There is one color-9 cell in every example and it stays fixed.
- The color-1 cells occur in the first row and disappear from the output. Their **count**, not contiguity, matters: the second training example has three non-prefix 1s and produces three orientations.
- Colors 2–8 make a motif relative to the 9. The output contains the motif at successive clockwise quarter-turns around the 9, preserving colors.
- Training example 1 has two 1s and shows the original plus a 90-degree clockwise copy.
- Training example 2 has three scattered 1s and shows original, 90-degree, and 180-degree copies.
- Training example 3 has four 1s and a two-color motif; all four orientations appear and both colors are preserved. This rejects both a prefix-tally rule and a color-6-only rule.

Implementation hypothesis: count first-row 1s as `K`; clear the canvas; retain the unique 9; for every input cell colored 2–8, place its original offset and its next `K-1` clockwise rotations around the 9. Clip an out-of-bounds rotated cell.

No accidental failed revision occurred. The only unobserved detail is ownership if differently colored rotations collide; none of the visible pairs has such a conflict. The implementation uses deterministic later-orientation overwrite.
