# Solve work log

## Exposure and allowed evidence

This is the required blind-before-repair episode. Before writing the solution I
read only the public preparation output, `solve-blind/README.md`, the template
`solution.py`, and this work-log template. I did not open any generator, Racket
rule, canonical database entry, prior solution, audit evidence, or private query
label. Earlier exposure to this task's rule: no.

## Revision 1 — translated template around every destination marker

All four demonstrations contain one color-9 cell embedded in a pattern of
color-4 cells and one or more separate color-2 cells. Treating the 9 as an
origin, the output removes the source pattern and translates every relative
4-offset to every 2. The 2s themselves remain as anchors.

The examples also expose two boundary/overlap details:

* translated cells outside the grid are clipped, as shown by markers near an
  edge;
* when a translated 4 would land on any original 2, the 2 remains visible, so
  destinations must be restored after painting the union of copies.

The implementation therefore finds the unique 9, records every 4 coordinate
relative to it, starts with an all-zero output of the same shape, paints those
offsets around each 2 when in bounds, then restores all 2 cells. A rectangular
input and exactly one 9 are checked explicitly. I retained no manufactured
failure because this first hypothesis accounts for every visible change and
for the clipped/overlapping cases.

Remaining uncertainty is limited to inputs outside the visible contract, such
as alternative colors or multiple 9s. The visible task consistently uses
0/2/4/9, so the submitted solver follows that observed color contract rather
than inventing a generalized color-role inference.
