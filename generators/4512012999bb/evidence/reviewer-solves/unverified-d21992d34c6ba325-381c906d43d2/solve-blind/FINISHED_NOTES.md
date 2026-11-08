# Solve work log

## Exposure declaration before solving

I had not seen task `4512012999bb`, its generator, Racket rule, private labels,
reference solution, or prior explanation. Before the assignment was drawn I did
open packet-level `WELCOME.md`, `RETURN-GUIDE.md`, and the generic `ARC-DESIGN.md`;
none contained this task's rule or examples. I used only the public examples
printed by `python3 solve_episode.py blind prepare` and files under
`solve-blind/` during this solve.

## Revision 1 — corner-marked frame receives the separate motif

**Hypothesis.** Each input contains (a) a sparse rectangle whose four corners
share one marker color and whose two side rails use two other colors, and (b) a
separate dense motif. The motif's bounding box has exactly the dimensions of the
rectangle's interior. The output is the cropped rectangle with the motif copied
unchanged into that interior; rails and corner markers remain in place.

**Evidence from visible examples.** The three frame/interior sizes are 8×8 / 6×6,
8×7 / 6×5, and 6×8 / 4×6. In every case the separate motif has the corresponding
interior size, and the displayed output is exactly the frame crop plus that
motif. Extra motif colors (1 and 7 in example 2) are copied rather than treated
as structural colors.

**Implementation.** Find the unique nonzero color occupying all four corners of
an axis-aligned rectangle. Treat nonzero cells outside that rectangle as the
motif, verify its bounding box matches the interior, crop the rectangle, and
copy the motif into cells one row/column inside the crop.

**Predicted queries.** Query 0 produces a 4×6 rectangle with color-4 corners,
color-2/1 side rails, and the 2×4 motif inserted. Query 1 produces a 7×8
rectangle with color-9 corners, color-8/5 rails, and the 5×6 motif inserted.

**Remaining uncertainty.** The visible data supports a unique four-corner marker
and a motif whose nonzero bounding box spans the full interior. I deliberately
reject broader alternatives such as recoloring the motif by side-rail identity:
example 2 shows non-rail colors survive unchanged.
