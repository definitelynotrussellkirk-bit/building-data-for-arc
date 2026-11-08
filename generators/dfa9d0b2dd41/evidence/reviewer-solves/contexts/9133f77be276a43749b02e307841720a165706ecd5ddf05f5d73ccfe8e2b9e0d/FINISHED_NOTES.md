# Post-repair visible-only solve notes

## Revision 1

Hypothesis from the displayed examples only:

1. Split nonzero cells into same-color, 4-connected objects.
2. Count occupied cells in each object and sort ascending. Train 1 is decisive: the five-cell L has a 3x3 bounding box but appears before the six-cell 2x3 rectangle, so the key is occupied-cell count, not bounding-box area.
3. Crop each object's bounding box, preserving internal zeros.
4. Top-align the crops left-to-right with exactly one zero column between consecutive crops.
5. For a size tie, use source top row then source left column; the examples have no tie, so this is the least additional deterministic assumption.

Predictions: query 0 orders colors 2 (2 cells), 5 (4), 6 (9); query 1 orders 8 (5), 3 (6), 4 (9). The L-shaped 8 crop must retain its two internal/background positions.

Uncertainty: tie behavior is not directly identified by the visible examples. The primary sorting rule and packing geometry are strongly identified, including a direct bounding-box-area counterexample.
