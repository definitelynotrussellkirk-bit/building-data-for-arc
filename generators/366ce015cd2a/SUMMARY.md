# 366ce015cd2a

0-bg grid (h ∈ 7-10, w ∈ 7-10) with: N_PAIRS ∈ 2-3 DIAGONAL ENDPOINT PAIRS — each pair consists of 2 cells of the SAME non-bg color (colors drawn WITHOUT REPLACEMENT from {1,2,3,4,6,7,8,9}), placed at endpoints of a 45° diagonal of LENGTH k ∈ 2-4 cells: A = (r1, c1) and B = (r1+k*sr, c1+k*sc) where sr, sc ∈ {-1, +1} (any of 4 diagonal directions). The interior cells along the diagonal are RESERVED (occupied set prevents other pairs from using them). Only the 2 endpoints are painted. Rule (FOR EACH COLOR APPEARING EXACTLY TWICE WHOSE CELLS LIE ON A 45° DIAGONAL (|DR| = |DC|), DRAW THE FULL DIAGONAL LINE BETWEEN THEM IN THAT COLOR): GROUP cells by color. For EACH color with exactly 2 cells: CHECK |dr| == |dc| (diagonal). PAINT every cell on the 45° line from endpoint A to endpoint B with that color. Net: endpoint pairs become solid diagonal colored lines.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
