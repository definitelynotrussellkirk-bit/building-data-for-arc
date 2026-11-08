# 8343e384cd7c

0-bg grid (h~5-7, w~5-7) with SPARSE NON-ZERO CELLS positioned in the UPPER PORTION (rows 0..h//2). 2-5 cells in random non-0 colors from {1..9} are placed at random non-overlapping positions in the upper rows. At least one cell is NOT in the last row (row h-1) so gravity has visible effect. Rule (GRAVITY DOWN AS A RIGID GROUP — SHIFT ENTIRE CONTENT DOWN UNTIL BOTTOM TOUCHES ROW h-1): compute max_r = MAXIMUM ROW INDEX of any non-0 cell. SHIFT = (h - 1) - max_r. For EACH NON-0 CELL at (r, c) with color C: ERASE (r, c) to 0 and PAINT (r + shift, c) with C. Net: the entire non-zero content translates down as a rigid block until its bottom-most cell sits on row h-1. Columns and colors preserved.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
