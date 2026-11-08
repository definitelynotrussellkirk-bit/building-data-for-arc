# ff973026bfbe

0-bg grid (h, w~6-10) with: (a) 1-3 COLOR-1 (blue) CELLS in DISTINCT rows (NOT row 0), each at a random column — these mark the 'active rows'; (b) 1-3 COLOR-2 (red) CELLS in ROW 0 at distinct random columns — these mark the 'active cols'. Rule (INTERSECT ROW-MARKS × COL-MARKS, PAINT 3): identify ALL ROWS containing a COLOR-1 cell (anywhere in that row) → mark_rows. Identify ALL COLUMNS where ROW 0 has a COLOR-2 cell → mark_cols. For EVERY (r, c) in mark_rows × mark_cols, PAINT the cell with COLOR 3 (green). The blue and red markers stay. Net: Cartesian product of row-1-marker rows × col-2-row-0 cols → green intersection grid.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.

## Native parametric sidecar

`workspace/parametric/` preserves the canonical rule as the default
`column_policy=all_top_markers` and adds
`column_policy=signal_ranked_marker`: count a neutral signal object and use that
one-based count to select which top-row red column is painted across the blue
rows.  It supports 2–6 demonstrations and 1–4 prefix-stable queries, including
a substantive 30×30 query.  This sidecar is qualified reviewer evidence only;
it is not production-integrated or admitted to training.
