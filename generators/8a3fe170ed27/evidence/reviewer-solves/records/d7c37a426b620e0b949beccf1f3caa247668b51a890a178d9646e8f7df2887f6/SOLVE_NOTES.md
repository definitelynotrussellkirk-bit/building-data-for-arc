# Visible-only solve notes

This is a human-readable work log based only on the displayed train examples in
this solve episode. I had earlier exposure to the selected task while reviewing
it, so the final declaration is `earlier-exposure yes`; I did not reopen or
consult the generator, Racket source, canonical ledger, prior explanations, or
private query labels during this solve phase.

## Hypothesis

The canvas size and colors stay fixed. Find the last nonempty row and treat it as
phase zero. Moving upward through occupied rows, translate each exact row by the
four-step horizontal cycle `0, left 1, 0, right 1`, indexed by absolute row
distance from that last nonempty row modulo four. Empty rows remain empty. Keep
all holes and row-specific details; cells shifted beyond a canvas edge disappear.

## Visible evidence

- In train 1, the last occupied row (row 12) is unchanged; row 11 loses its
  left-edge cell and moves the right rail from column 8 to 7, establishing a
  one-cell left shift at distance 1.
- Row 10 is unchanged at distance 2, while row 9 moves both rails right by one
  at distance 3. Row 8 is unchanged again at distance 4.
- The other demonstrations repeat the same phase pattern on bars, rails, holes,
  and both edges, so this is exact row translation rather than reconstruction of
  a rectangle or shared rails.

`solution.py` implements that rule directly and is shape-preserving for empty or
ordinary rectangular grids.
