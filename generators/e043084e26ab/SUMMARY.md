# e043084e26ab

0-bg grid (h ∈ 9-11, w ∈ 11-13) with four singleton marker cells in colors 2, 3, 4, and 6 at randomized non-overlapping positions, plus one connected color-1 template (line or L triomino) and one non-cyan decoration in color 7 or 9. Rule: compute v = (pos(3)-pos(2)) + (pos(6)-pos(4)); for each color-1 template cell, paint color 8 at the translated cell when it is in-bounds and background. Normal generation guarantees the translated template cells are in-bounds/background so the cyan copy is fully visible.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
