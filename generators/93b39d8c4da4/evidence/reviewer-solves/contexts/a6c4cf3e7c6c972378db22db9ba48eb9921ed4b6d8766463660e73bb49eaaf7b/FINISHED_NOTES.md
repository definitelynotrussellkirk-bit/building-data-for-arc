# Exposed post-repair solve work log

This is a human work log based only on `solve/challenge.json` after preparation.
I had earlier rule exposure during the generator review, so this episode is not blind.
I did not reopen the generator, Racket source, reference solution, or private labels during this solve phase.

## Visible-example hypothesis

Across all four demonstrations, the color-2 cells form one compact template. The output discards the input objects, tight-normalizes that template by its bounding box, and copies it in color 8 with the normalized `(0,0)` aligned to every color-3 cell. Multiple copies are unioned on a fresh zero canvas. The fourth demonstration is especially useful because the five-cell template and three anchors rule out treating the red object as output content or merely recoloring green cells.

## Revision 1

Implement exactly that transform: collect the red template, subtract its minimum row and column, collect all green anchors, and stamp every normalized offset in cyan on a blank grid. I included bounds clipping defensively, although the visible examples place all copies in bounds.
