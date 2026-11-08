# 5c6b3679aff9

0-bg grid (h, w ∈ 6-18, by difficulty) with: (a) N_BLOCKS ∈ 1-4 SOLID 2×2 BLOCKS, each in a color drawn from a 2-7 color palette, placed per BLOCK_POSITION_BIAS ∈ {spread, center, edge} with ≥2-cell separation between blocks; (b) N_ISOLATED ∈ 2-10 SCATTERED SINGLE CELLS, each in a random palette color, placed at positions where they have NO same-color neighbor within ISOLATED_SEPARATION (default 1) — so each isolated cell is TRULY ISOLATED (not part of a 2×2 same-color block). Rule (KEEP CELLS THAT ARE PART OF A 2×2 SAME-COLOR BLOCK; ERASE ALL OTHER NON-BG CELLS TO 0): SCAN every 2×2 window of the grid. IF a 2×2 window has all 4 cells of the SAME non-bg color: MARK those 4 cells as 'keep'. After scanning all windows: PAINT non-kept non-bg cells to 0. Net: solid 2×2 blocks survive in their color; isolated cells vanish.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
