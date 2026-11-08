# Solve work log

## Exposure declaration before solving

I had not opened the task's generator, Racket rule, private labels, reference
solutions, notes, or audit evidence. I used only the visible examples printed by
`python3 review.py blind prepare` and `challenge.json`.

## Revision 1 — marked component extraction

Hypothesis: one non-background color is marked by a disconnected singleton. The
same color also contains the payload shape, sometimes alongside another small
decoy component. Select that color, keep its largest 4-connected component,
crop to its bounding box, and replace every source cell by a 2×2 block.

Evidence from the three demonstrations:

- Example 0: color 7 has a singleton plus a seven-cell `111/001/111` payload;
  doubling it gives the 6×6 output.
- Example 1: color 4 has a singleton, a two-cell decoy, and the largest
  `10/11/01` payload; doubling the largest component gives the output.
- Example 2: color 1 has a singleton plus a five-cell cross; doubling the cross
  gives the output.

The two queries predict, respectively, a doubled color-4 cross (6×6) and a
doubled color-1 `011/110` shape (4×6). Remaining uncertainty: the visible data
do not prove how to break a tie between multiple colors carrying singleton
markers. The implementation chooses the candidate with the largest payload.
