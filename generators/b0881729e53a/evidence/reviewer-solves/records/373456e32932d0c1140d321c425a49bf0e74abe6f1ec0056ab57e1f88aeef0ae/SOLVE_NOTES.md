# Solve work log

## Exposure declaration

This is a human work log. I had already reviewed and repaired this generator before the required post-repair episode, so earlier rule exposure is **yes**. During this solve phase I used only the visible examples printed by `review.py solve prepare`; I did not reopen the Racket authority, generator source, private labels, reference solutions, or an earlier solution explanation.

## Revision 1 — move the row-major-last external component into the frame

Each example contains one complete hollow rectangular frame and one or two monochrome external components. The output erases all external source cells, preserves the frame, crops the external component whose first cell appears last in row-major component discovery, and pastes that crop unchanged at the floor-centered position inside the frame interior.

The demonstrations rule out several simpler selectors: examples 0 and 1 choose the left-hand/lower component rather than the rightmost component; examples 2 and 3 have same-row components, making the later start column decisive. Shape, size, color, and frame distance are tied or reversed across examples. I implemented same-color four-connected components, exact hollow-frame recognition, row-major discovery order, source erasure, crop normalization, and floor centering. Remaining uncertainty is only the intentionally masked query labels.
