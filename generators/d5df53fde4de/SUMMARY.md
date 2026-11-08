# d5df53fde4de

0-bg grid with: (a) one KEY cell at the TOP-RIGHT corner (0, w-1) in some non-bg color cK; (b) 2-3 NON-RECTANGULAR blobs in distinct non-cK colors, placed in the interior. Each blob is 4-connected with bbox dims ≥2×2 and SHAPE differs from its bbox (so the rule's bbox-fill is visible). Rule: read key = g[0][w-1]. For each non-key blob, compute its bbox. Paint all cells in the bbox (including any bg holes) with the key color. Key cell preserved.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
