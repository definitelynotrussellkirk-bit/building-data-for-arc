# f5b97ca6690b

0-bg grid (h = n, w = 3n+2 where n ∈ {4..8}) split into 3 EQUAL-WIDTH N×N PANELS by 2 full-height COLOR-9 (maroon) DIVIDER columns at cols n and 2n+1. Panel A (cols 0..n-1) contains a small connected MULTI-COLOR SHAPE using 2-4 colors from a SOURCE PALETTE drawn from {2..8}; every source-palette color appears at least once. Panel B (cols n+1..2n) contains the SAME SHAPE at the same positions, but each cell is recolored via a fixed bijection src→tgt (the cmap) where tgt-palette is disjoint from src. Panel C (cols 2n+2..3n+1) contains an INDEPENDENT shape using only SOURCE-PALETTE colors. Rule: infer the A→B color MAPPING (a permutation/bijection) by scanning corresponding cells. CROP panel C to its content and RECOLOR every non-bg cell via that A→B mapping. Output the mapped C. Net: A→B teaches a color permutation; output is C with that permutation applied.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
