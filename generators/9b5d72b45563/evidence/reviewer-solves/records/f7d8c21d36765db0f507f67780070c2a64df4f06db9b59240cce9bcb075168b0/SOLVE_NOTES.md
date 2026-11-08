# Visible-only solve work log

This is a human work log based only on the prepared visible examples. I had earlier rule exposure from the generator review, so this is not a blind record; I did not consult generator or Racket source after preparation.

## Hypothesis

Each nonzero input cell is a seed. Start with an all-zero grid of the same dimensions. For each seed, retain the center and add the four one-step diagonal cells, producing an X of up to five cells. Clip arms that leave the grid.

Train example 2 distinguishes collision order: the row-4 seeds at columns 3 and 5 share diagonal target cells at `(3,4)` and `(5,4)`. Those cells are color 7, so processing is row-major and the later/right seed overwrites earlier paint. Train example 0 confirms all four seeds matter, repeated colors are independent seeds, and border clipping is used.

## Implementation

Scan rows top-to-bottom and columns left-to-right. Paint `(0,0)`, `(-1,-1)`, `(-1,+1)`, `(+1,-1)`, and `(+1,+1)` offsets on a fresh zero canvas. Ordinary assignment naturally implements later-writer precedence.
