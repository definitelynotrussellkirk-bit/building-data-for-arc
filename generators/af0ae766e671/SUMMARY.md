# af0ae766e671

Grid is 2*half_h × w (half_h~3-7, w~3-14): TOP HALF (rows 0..half_h-1) filled with TOP_COLOR cells (non-{0, 6}) at random density; BOTTOM HALF (rows half_h..2*half_h-1) filled with BOT_COLOR cells (non-{0, 6, top_color}) at random density. Both halves use the same PATTERN (random/blob/stripes/checker/border/diagonal). At least one cell differs in zero-occupancy across the two halves. Rule (ZERO-OCCUPANCY XOR → 6): OUTPUT is half_h × w. For EACH OUTPUT CELL (r, c): compute (input[r][c] == 0) XOR (input[half_h + r][c] == 0). If XOR is TRUE (exactly one of the two halves has 0 at that cell), set output to COLOR 6 (magenta). Otherwise 0. Net: 2-stacked halves → 1-height output marking where zero-occupancy differs.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
