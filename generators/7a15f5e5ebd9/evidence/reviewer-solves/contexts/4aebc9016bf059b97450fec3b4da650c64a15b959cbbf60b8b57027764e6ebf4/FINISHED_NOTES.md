# Solve work log

## Exposure statement

Before this solve I had read only the packet-level instructions and the drawn
assignment. I did not open this task's generator, canonical rule, reference
solution, private labels, audits, or any earlier explanation. The visible grids
printed by `python3 review.py blind prepare` were my only task evidence.

## Revision 1 — anchored template stamping

Hypothesis: color 9 is an anchor embedded in a color-4 template. Each color-2
cell is a destination anchor. The output erases the source template, preserves
all color-2 destination cells, and copies every color-4 cell at the same offset
from each destination that it had from color 9. Copies outside the grid are
clipped. If a copied color-4 cell lands on a color-2 cell, color 2 remains.

Evidence and probes:

- Example 0: relative to 9 at `(1, 0)`, the five yellow offsets are
  `(-1,0), (0,1), (1,0), (1,1), (1,2)`. Those exact offsets appear around each
  of the three red cells.
- Example 1: with the red cell at `(0,0)`, only three of the six yellow offsets
  remain in bounds; the output contains exactly those three cells. This supports
  clipping rather than translating the stamp to fit.
- Example 2: the lowest stamp loses its `(2,1)` cell beyond the bottom edge.
- Example 3: one copied yellow cell would overlap another red marker; the marker
  remains red, establishing marker priority.

Implementation extracts the yellow offsets from the unique 9 anchor, creates a
blank output of the same dimensions, writes the red markers, then writes all
in-bounds yellow offsets without overwriting red markers.

Remaining uncertainty: the visible examples contain one color-9 anchor and only
colors 0, 2, 4, and 9. I assume those are task invariants. The two hidden query
outputs remain unavailable by design.
