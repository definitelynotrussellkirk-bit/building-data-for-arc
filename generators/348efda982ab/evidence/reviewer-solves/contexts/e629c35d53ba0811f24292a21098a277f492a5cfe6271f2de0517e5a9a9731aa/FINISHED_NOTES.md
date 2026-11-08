# Solve work log

I had not opened this task's generator, reference rule, private labels, notes, prior solutions, or the assigned repair generator before this blind solve. I used only `solve-blind/challenge.json` and visible-example tests.

## Revision 1 — room marker count equals door count

The blue cells form rectangular room walls. Orange cells are one-cell doorways in those walls, and green cells are markers inside rooms. In every training pair, the output first erases all green markers. It then fills an entire room azure exactly when the number of green markers originally inside that room equals the number of distinct orthogonally adjacent orange doorway cells incident to that room. This also explains the isolated lower-left room in training example 2: it has zero markers and zero doors, so it is filled.

I checked the hypothesis manually across all visible rooms. In training example 3 all six rooms have two doors; exactly the three rooms with two green markers are filled. A count-only threshold and graph-reachability rule were considered and rejected because training example 2 contains rooms with the same marker count but different door degrees and different outputs.

Implementation plan: treat blue and orange cells as barriers, flood-fill each remaining room, count original green cells and distinct adjacent orange cells, fill the room with 8 on equality, otherwise convert only green to 0, and preserve walls/doors. A visible-pair pytest was written first and failed on the prepared `NotImplementedError`; the implementation then passed all three visible training pairs.

Remaining uncertainty: unseen inputs may contain irregular rooms, but component-based room discovery and distinct-door counting do not depend on rectangles or fixed room sizes.
