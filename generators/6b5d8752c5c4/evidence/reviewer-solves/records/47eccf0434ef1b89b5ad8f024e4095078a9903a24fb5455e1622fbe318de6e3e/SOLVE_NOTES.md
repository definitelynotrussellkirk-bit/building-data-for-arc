# Solve work log

## Prior exposure

Before this blind solve I had read only the packet-level instructions and the drawn assignment. I had not opened task `6b5d8752c5c4`'s generator, Racket rule, canonical row, prior notes, reference solutions, private query labels, or audit records.

## Revision 1 — split at the colored seam and move the pieces apart

Observation: every nonzero object is mostly color 9 plus a rarer color. In the outputs the rarer cells disappear, the color-9 count is preserved, and the remaining shape is separated by one extra blank row or column. The rarer cells form a zigzag cut across the full object: a top-to-bottom cut separates left/right pieces; a left-to-right cut separates top/bottom pieces.

Hypothesis: find each 4-connected non-background object, remove its rare-color seam, find the resulting 4-connected body pieces, and translate each piece one cell away from the seam. Use the seam's boundary contacts to choose the movement axis. This explains the bent seams, the checkerboard two-row cut, the multiple independent objects, and the unchanged output dimensions.

Probe: added `test_solution.py`, which checks all three visible training pairs. It first failed with the template's `NotImplementedError`, then passed after implementing the component/seam algorithm. Command: `python3 solve-blind/test_solution.py` from the packet root.

Alternatives rejected: merely recoloring the seam cannot explain the shifted coordinates; shifting every row around its own marker is less robust for horizontal seams; using bounding rectangles alone is unnecessary because connected components directly recover the two pieces.

Remaining uncertainty: unseen inputs could use a nonzero background, more than two foreground colors, or a seam that does not disconnect the body into two pieces. The visible lesson consistently has one dominant background, one body color, and one rarer seam color, so the solution infers those roles by frequency and preserves body cell colors while moving components.
