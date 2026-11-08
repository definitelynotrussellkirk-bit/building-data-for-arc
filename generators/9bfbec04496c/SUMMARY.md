# 9bfbec04496c

Fixed 8×8 grid laid out as 3×3 tile-mosaic: each tile is 2×2, separated by full-width SEPARATOR rows at rows 2 and 5 and full-height SEPARATOR cols at cols 2 and 5 (all painted with a sep-color, drawn from palette). Each 2×2 tile is a copy of the same BASE TILE except for 1-2 MUTATED cells which differ. Rule: detect separator rows/cols → tile size 2×2. Collect all 9 tiles. Output is the 2×2 tile: cell (r, c) = base value if all 9 tiles agree; if ≥2 tiles disagree → cell = 1 (blue). Net: the consensus tile with disagreements marked in color 1.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
