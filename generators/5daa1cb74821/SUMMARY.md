# 5daa1cb74821

0-bg grid (h~5-7, w~6-8) with: (a) TOP LEGEND — row 0, cols 1..w-1, holds a sequence of (potentially repeating) colors from palette {2, 3, 4, 5, 6, 7} (one per column); (b) LEFT LEGEND — col 0, rows 1..h-1, holds a sequence of colors from the same palette (one per row); (c) (0, 0) is 0; (d) interior cells (rows 1..h-1, cols 1..w-1) are 0. At least one (left[r] == top[c]) MATCH exists. Rule (ROW × COLUMN COLOR-MATCH MAP, INTERIOR-ONLY OUTPUT): output is a (h-1) × (w-1) GRID. For each output (r, c) with r ∈ [0, h-2], c ∈ [0, w-2]: if LEFT[r] == TOP[c] AND non-zero, PAINT (r, c) with that shared color. Else 0. The row 0 and col 0 legends are discarded. Net: produces a row × col match matrix where matching cells get their shared color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
