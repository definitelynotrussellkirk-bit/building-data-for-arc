# a5557bf1391e

0-bg grid (h~6-10, w~4-7) with: (a) ONE FULL-WIDTH FLOOR ROW of COLOR 8 at the BOTTOM (row h-1, all cols painted 8); (b) 2-3 HORIZONTAL COLORED BARS above the floor — each bar is 1 ROW TALL, has a chosen LENGTH from 1..w-1 in a DISTINCT NON-8 color from a palette ({1, 2, 3, 4, 6, 7, 9} or kind-restricted), placed at distinct rows in [0, h-2] with position bias (scattered/left-lean/right-lean/centered) and size skew (small/big/even). Bars don't overlap. Rule (SORT BARS BY SIZE DESC, PACK BOTTOM-RIGHT ABOVE FLOOR): identify all colored bars (each its own row segment) and their lengths. SORT by LENGTH DESCENDING (biggest first, tiebreak by color). Output is a fresh grid same h × w with the floor row preserved at the bottom (row h-1 = 8s). Pack the sorted bars STACKED bottom-up, RIGHT-ALIGNED, each on its own row immediately above the floor (row h-2, h-3, h-4, ...). Net: bars sorted big-to-small, right-stacked on top of the 8-floor.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
