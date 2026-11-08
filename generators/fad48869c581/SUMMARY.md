# fad48869c581

0-bg grid (h~6-9, w~6-9) with 2-4 ISOLATED 2×2 BLOCKS placed at non-touching positions (3-cell pairwise padding guard). Each block: pick a non-0 color from {1..9}; pick one of the 4 CORNERS as the MISSING corner; PAINT the other 3 corners with the chosen color. The fourth corner stays bg-0. Each block thus presents an L-triomino with one empty corner. Blocks are widely separated to avoid accidental completions. Rule (COMPLETE EACH 2×2 BLOCK BY FILLING ITS MISSING CORNER WITH THE BLOCK'S COLOR): for EACH 2×2 WINDOW that has EXACTLY 3 cells of ONE non-0 color C and the FOURTH cell = bg-0: RECOLOR the missing-corner 0 cell to C. The other cells stay. Non-active 2×2 windows (with different color counts or all bg) are unchanged. Net: each L-triomino is closed into a solid 2×2 monochrome square.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
