# Solve work log

## Prior exposure

This is **not a blind solve**. Before this phase I reviewed the assigned generator and its selected authority while repairing it. During this solve I kept those files closed and used only the visible challenge presentation plus my own Python. I did not consult private query labels or a reference solution during the solve.

## Revision 1 — component selection by a grown contact score

The inputs contain several four-connected color-2 motifs and a separate color-1 mask. Every output is a tight crop of one original color-2 motif, preserving holes inside its bounding box but recoloring occupied cells to 8.

Visible probes:

- Train 0's 2×3 output exactly matches the upper-right motif, not its expanded footprint.
- Train 2's 3×4 output matches the lower-right motif; it is the motif whose one-cell square expansion covers the most color-1 cells.
- Train 3 is useful because the output is the isolated cell near the mask rather than the earlier vertical motif. Their expanded footprints have equal zero overlap, so proximity must break that tie.
- A final deterministic reading-order tie-break is needed when overlap and proximity are both equal; top-left component order is the simplest rule consistent with the examples.

Hypothesis: expand each color-2 component hypothetically by one cell in all eight directions. Rank components by (1) maximum overlap with color 1, (2) minimum Manhattan distance from the expanded footprint to color 1, and (3) top-left reading order. Crop the selected **original** component and recolor it 8.

I implemented this directly with independent four-connected component extraction. Expected query shapes from the visible inputs are 1×1 for query 0 and 3×4 for query 1, but the program derives them rather than hard-coding them.
