# ee822284e294

0-bg grid (h~9-11, w~11-13) with exactly 3 SINGLE-CELL MARKERS in distinct non-zero colors. Markers are placed with Manhattan distance ≥ 3 from each other (so they don't touch and the L-paths are visible). They should not all share the same row/column (non-collinear). Rule: for each color-object, compute its bbox center (integer midpoint). Sort markers by color value ascending. For each consecutive PAIR of sorted centers (a, b): draw a HORIZONTAL segment from (r_a, c_a) to (r_a, c_b) painted with color_a, then a VERTICAL segment from (r_a, c_b) to (r_b, c_b) painted with color_a (the FIRST marker's color of the pair = smaller color). Finally re-paint each original marker on top. Net effect: L-paths connect color-sorted markers, each L colored by the smaller of the pair.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
