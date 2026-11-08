# 5b4fd0a9c80e

0-bg grid (h~10-12, w~11-13) with: EXACTLY 3 NON-OVERLAPPING COMPONENTS each in a DISTINCT non-bg color drawn from {1,2,3,4,6,7,8,9}. The three sizes are sampled WITHOUT REPLACEMENT from {3, 4, 5, 6, 7} (strictly distinct cell counts) and each shape comes from _BY_SIZE bank (L-tromino / Z-tromino / square / T / row / L-5 / C-7) — placed with 1-cell padding via _free check. Rule (SORT BY (SIZE, ROW, COL) THEN VSTACK BBOX CROPS CENTER-ALIGNED WITH 1-ROW GAPS): FIND every 4-connected non-bg COMPONENT. SORT components by (cell_count, bbox_top_row, bbox_left_col) ASCENDING. CROP each to its bbox. VERTICALLY STACK the crops with a 1-ROW GAP between, center-aligned horizontally so the widest component sets the output width. OUTPUT the stacked column. Net: the 3 components are extracted and laid out top-to-bottom by ascending size, gaps between, centered.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
