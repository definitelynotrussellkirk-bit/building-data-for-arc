# 7a8926bd9d9f

0-bg grid (h~8-10, w~8-10) with 2-3 PAIRS of OPPOSITE-CORNER CELLS in DISTINCT colors from {1..9}. Each PAIR has two cells placed at DIAGONALLY OPPOSITE CORNERS of an axis-aligned rectangle of size 2-4 × 2-5 (TL/BR OR TR/BL, randomly chosen). The rectangles between pairs are DISJOINT (no cell shared). Rule (FILL EACH OPPOSITE-CORNER PAIR'S BOUNDING RECTANGLE WITH ITS COLOR): For EACH COLOR appearing as EXACTLY 2 CELLS at (r1, c1) and (r2, c2) — diagonal corners of an axis-aligned rectangle: PAINT every cell at rows min(r1, r2)..max(r1, r2), cols min(c1, c2)..max(c1, c2) (inclusive — the full filled rectangle) with that color. Net: each pair of diagonal corners fills in to a solid rectangle of its color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
