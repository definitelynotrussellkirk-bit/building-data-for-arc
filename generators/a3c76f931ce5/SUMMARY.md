# a3c76f931ce5

size × size grid (~7-10) with: (a) outer bg = 0; (b) a SOLID INTERIOR RECTANGLE in some non-{0,2,4} color filling rows 1..size-2, cols 1..size-2; (c) a 2×2 (or 3×3) HOLE of 0s strictly inside the colored rect. Rule: compute sc = mode color (the rect's color). For each color-sc cell with EXACTLY 2 same-color cardinal neighbors that form an L (NOT up+down or left+right) — that's a CORNER. Pick the diagonal cell INWARD from the corner. If that diagonal cell is 0 AND fully enclosed (border-unreachable through bg) → mark corner with color 2 (red). Else mark with color 4 (yellow). Net: each of the 4 inner corners of the rect-frame around the hole gets marked.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
