# 0cf12bd584ef

0-bg grid (h ∈ 7-9, w ∈ 8-10) with: (a) A 2-ROW LEGEND at TOP — for each of 2 DISTINCT COLUMNS (cols sorted, drawn from range(w)): row 0 holds a SRC color, row 1 holds the matching DST color. The 4 colors (src1, dst1, src2, dst2) are drawn distinct from {2..9}; (b) BELOW ROW 1 (row 2 is buffer): TWO BLOBS, each in one of the SRC colors (src1 or src2), built via grow_blob of 2-3 cells, placed at non-overlapping interior positions. Rule (READ THE 2-ROW LEGEND TO BUILD A RECOLOR MAP SRC→DST; FOR EACH NON-BG BODY CELL (R ≥ 2) WITH COLOR V: IF V IS A SRC: PAINT g[R][C] = MAP[V]; ELSE: KEEP AS-IS): PARSE the top 2 rows to build (src1→dst1, src2→dst2) map. For EACH cell (r, c) below row 1: IF g[r][c] ∈ map: PAINT g[r][c] = map[g[r][c]]. Legend rows preserved (or per demos, zeroed). Net: src-colored blobs are recolored to their corresponding dst colors per the legend.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
