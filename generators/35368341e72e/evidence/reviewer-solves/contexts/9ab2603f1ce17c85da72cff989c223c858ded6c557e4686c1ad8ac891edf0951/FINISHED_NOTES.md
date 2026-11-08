# Solve work log

## Exposure

Before this solve I had read only the packet-level start/duties instructions and the visible presentation produced by `blind prepare`. I did not open any generator, Racket rule, canonical answer, prior solution, audit evidence, or private query label for task `35368341e72e`.

## Revision 1 — dictionary of labelled 3×3 tiles

**Observation.** The first row is a key. Each nonzero key cell sits one column above the center of a 3×3 tile occupying rows 1–3. The final row is a request sequence: read its nonzero marker colors from left to right. The output is the requested tiles in that order, with one all-zero separator column between adjacent tiles.

Evidence from the visible examples:

- Example 0 has one key marker `6` above the 3×3 color-8 tile and two `6` request markers, so the output is two copies of that tile.
- Example 1 maps key marker `8` to the middle 3×3 color-4 tile; the two final-row `8`s request two copies.
- Example 2 maps `3` to the tile centered at column 6 and `9` to the tile centered at column 3. The final-row sequence `3,9,9` exactly matches the three output blocks.

**Rejected alternatives.** Initially the output could have looked like duplicating a salient object or selecting the densest tile, but example 2 rules those out because it requests two different mapped tiles in a specific order.

**Implementation.** Build a marker→tile dictionary from nonzero cells of the first row, then concatenate tiles named by nonzero cells of the last row. I kept the inferred fixed 3×3 tile size because all three visible examples support it and each marker is centered over exactly three columns.

**Predicted queries.** Query 0 requests key colors `8,5,5`; query 1 requests `7,7`. The checker is used only for visible examples and execution; masked outputs remain unknown.

**Remaining uncertainty.** The visible data does not test duplicate key colors or a marker at the grid edge. The demonstrated construction places unique key colors away from edges, so the solution follows that contract rather than inventing fallback behavior.
