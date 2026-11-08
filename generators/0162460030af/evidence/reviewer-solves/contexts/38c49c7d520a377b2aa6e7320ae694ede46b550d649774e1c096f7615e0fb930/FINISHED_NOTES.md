# Solve work log

## Exposure declaration before work

I had not opened this task's generator, Racket rule, notes, reference solutions,
private labels, or audit evidence. I used only the visible grids in
`challenge.json` and local Python calculations over those grids.

## Revision 1 — alternating object chain, centred phase

The transformation preserves every non-background object's cells while replacing
its colour by red (2) or azure (8). Component size and original colour are not the
criterion: the examples split identical 2x2 squares, single cells of three input
colours, and two same-colour L triominoes.

I extracted 4-connected same-colour components and compared their centroids. In
all visible examples they form a left-to-right chain. The output alternates by
chain position, but the phase is not always "leftmost is red": with three objects,
the middle object is red and both endpoints are azure. A single rule fitting all
three examples is therefore:

1. order objects by horizontal centroid;
2. choose the left of the two middle positions when the count is even;
3. colour that middle position red, then alternate red/azure in both directions.

This predicts query 0's upper middle square as red and both lower endpoint squares
as azure. For query 1 it predicts red on chain positions 0, 2, and 4 (the left L,
vertical domino, and upper-right L) and azure on positions 1, 3, and 5.

Alternative considered: root the alternation at the object nearest the whole-grid
centre. That also fits the training examples but disagrees on query 1. I rejected
it because the examples visibly organize the objects as an ordered chain, and the
phase is naturally specified by the chain's middle rather than by unused empty
margins of the canvas.
