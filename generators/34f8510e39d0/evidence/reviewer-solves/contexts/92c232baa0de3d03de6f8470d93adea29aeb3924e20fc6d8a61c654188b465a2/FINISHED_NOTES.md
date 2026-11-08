# Solve work log

## Exposure declaration before solving

I had not opened task `34f8510e39d0`'s generator, Racket rule, notes, private
answers, prior solutions, or audit evidence. I used only the visible examples
printed by `python3 review.py blind prepare` and the generated public README.

## Revision 1 — orthogonal boundary recoloring

### Observation

Across all three demonstrations, only color 3 changes. Every color-3 component
is a filled rectangle. Cells on each rectangle's outside boundary become color
8, while cells with green neighbors above, below, left, and right remain color
3. Thin rectangles have no such interior cells, so they become entirely color
8. The second nonzero color (9 or 6) is unchanged and appears to be a distractor.

The examples distinguish this from “recolor every 3” because the 4×4 and 5×4
rectangles retain their centers. They also distinguish a fixed one-cell inset
of a single bounding box from component-wise handling because examples 0 and 2
contain a separate 2×3 green component that must become entirely azure.

### Program

Copy the grid. For each cell of color 3, keep it green exactly when all four
orthogonal neighbors exist and are also color 3; otherwise recolor it to 8.
Leave all other colors unchanged.

### Predicted queries

- Query 0: the 4×3 green rectangle keeps its two middle-column interior cells;
  the 3×3 rectangle keeps only its center. All other green cells become 8.
- Query 1: the 2×3 rectangle becomes all 8; the 4×4 rectangle keeps its central
  2×2 green block. Color 6 remains unchanged.

### Remaining uncertainty

The visible data contains only rectangular green components, so an equivalent
rectangle-border implementation would also fit. The local four-neighbor test is
the simpler shape-general statement of “exposed boundary” and exactly matches
all visible examples without using the unrelated colored object.
