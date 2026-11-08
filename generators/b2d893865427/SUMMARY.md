# b2d893865427

0-bg grid (h, w ~ 9-17) with 3-5 (or up to 6 hard) SOLID 2×2 BLOCKS placed at random non-overlapping non-touching positions (1-cell padding via _free). Each block is painted entirely in a DISTINCT non-0 color drawn from a shuffled palette {1..9}. Block top-left positions may share rows, share cols, or be all distinct (per position_bias). Rule (PROJECT 2×2 BLOCKS TO A MINI GRID — ROWS = SORTED UNIQUE BLOCK TOP-ROWS, COLS = SORTED UNIQUE BLOCK TOP-COLS): scan the grid for SOLID 2×2 monochromatic BLOCKS. For EACH block, record its top-left (top_row, top_col) and color. EXTRACT SORTED UNIQUE top_row values → rows[0..M-1]. EXTRACT SORTED UNIQUE top_col values → cols[0..N-1]. PRODUCE an M × N OUTPUT grid where output[r][c] = block_color whose (top_row, top_col) = (rows[r], cols[c]), or 0 if no block sits at that intersection. Net: the scattered 2×2 blocks become a small mini grid encoding their projection onto unique row/col positions.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
