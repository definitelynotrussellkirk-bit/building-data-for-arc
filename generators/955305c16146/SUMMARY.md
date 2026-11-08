# 955305c16146

0-bg grid (h, w~4-18) with n_rows_with_dots active rows containing COLOR-1 (blue) DOTS in one of 4 LAYOUTS (endpoints / scattered / regular_spacing / triple_anchors), with DOT_COUNT distribution sparse_2/cluster_3plus/dense_5plus/mixed. Row distribution: top_only/bottom_only/spread/alternating/all_rows. Plus optional 0-3 DECOY COLORS in non-trigger rows. At least one row has ≥2 dots with bg between them. Rule (PAINT RED BETWEEN BLUE DOTS PER ROW): for EACH ROW, find the COLUMNS of all COLOR-1 cells. If ≥2 dots, find LEFTMOST and RIGHTMOST. PAINT every BG (0) CELL strictly BETWEEN them in that row with COLOR 2 (red). Rows with <2 dots stay. Decoys (non-1) cells stay. Net: each row with ≥2 blue dots fills its bg span between leftmost and rightmost dots with red.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
