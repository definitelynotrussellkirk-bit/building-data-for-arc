# 3b5ec9768247

0-bg grid (h×w, ~7-10 by ~8-12) with exactly 4 non-zero cells all of the SAME color, placed at the 4 corners of an axis-aligned rectangle (r1, c1), (r1, c2), (r2, c1), (r2, c2). The rectangle has h ≥ 3 and w ≥ 3 (so the border is visible). Rule: collect all non-zero cells, read their common color, compute bbox. Build output: fresh 0-canvas with a HOLLOW RECTANGLE (border only, interior 0) drawn at the bbox in that color. The 4 input corners are preserved; edge cells between them are filled in.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
