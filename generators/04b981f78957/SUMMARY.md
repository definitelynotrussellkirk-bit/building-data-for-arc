# 04b981f78957

Small grid (h, w ∈ [3, 7]) with 2-6 MARKER CELLS in 1 OR 2 non-{0, 2} colors placed at interior positions via layout (random/cluster/diagonal/scattered/blob/row/column/corners) and position bias (top/bottom/center/spread). Rule (DIAG-SHADOW THEN 3×3 TILE): (i) BUILD a SHADOWED TILE from the input: for EACH (r, c) where g[r][c] == 0, if g[(r+1) % h][(c+1) % w] is NON-ZERO, PAINT (r, c) WITH COLOR 2. Existing non-0 cells stay. (ii) TILE the shadowed input INTO A 3h × 3w OUTPUT by repeating it 3 × 3 times. Net: each empty cell with a diagonal-neighbor non-zero becomes 2; then the whole tile repeats 3 × 3.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
