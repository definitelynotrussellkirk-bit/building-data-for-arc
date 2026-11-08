# Solve work log

## Exposure declaration before solving

I had not opened task `0b9e771d6ba5`'s generator, rule, notes, solutions, audit
records, or private labels. I used only `solve-blind/challenge.json` and my own
Python analysis. I had read the packet workflow documents and the assignment.

## Revision 1 — complete interrupted non-background rectangles

Across the three visible examples, the changed color's axis-aligned bounding box
was fully occupied by non-background cells, but some cells in that box had been
painted by other colors. Repainting that box with its owning color exactly explains:

- the six `5` cells enclosed by the `9` box in train 0;
- both interrupted horizontal bars (`9` and `1`) in train 1; and
- the twenty-five `9` cells inside the incomplete `8` box in train 2.

The small two-color zigzags are not changed because each color's bounding box
contains background. Already-solid rectangles are not candidates because their
box needs no repair.

I implemented that rule directly. The first masked input contains two inferred
one-cell-wide rectangles whose boxes cross at one cell, a case not resolved by
any visible output. I chose the larger-area rectangle at a conflicting claim,
then more visible support and first appearance as deterministic tie-breakers.
The main uncertainty is this overlap policy; preserving the occluder or giving
the smaller inferred box priority are also compatible with the visible examples.
