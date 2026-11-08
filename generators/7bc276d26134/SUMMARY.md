# 7bc276d26134

0-bg grid (h~8-10, w~9-11) with: (a) cell (0,0) = TRANSFORM CODE value in {1..7}; (b) one connected ASYMMETRIC shape (3-5 cells) of a single non-bg color, placed in the interior (not touching (0,0)). Rule: read code = grid[0][0]. Clear (0,0) to 0. Crop the rest of the grid to its non-zero bbox (the shape). Apply transform: 1 → identity, 2 → rotate-CW, 3 → rotate-180, 4 → rotate-CCW, 5 → flip-LR, 6 → flip-UD, 7 → transpose. Output is the transformed crop (small grid).

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
