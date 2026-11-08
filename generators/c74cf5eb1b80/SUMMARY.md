# c74cf5eb1b80

0-bg grid (h~6-10, w~9-14) with: (a) EXACTLY ONE FULL-HEIGHT color-9 (maroon) DIVIDER COLUMN at some column gc placed in the right half of the grid (gc ∈ [w//2..w-2]); (b) scattered non-{0, 9} content cells in 2-3 distinct colors placed ONLY on the LEFT side of the divider (cols 0..gc-1), at random row positions. The RIGHT side (cols gc+1..w-1) is initially EMPTY. Rule: for each cell (r, c) on the LEFT side with non-zero non-9 color k, compute its MIRROR column mc = 2*gc - c. If (r, mc) is in bounds, PAINT (r, mc) with color k. The 9-divider stays; original left cells stay. Net: the maroon column acts as a vertical mirror, reflecting all left-side content into the right half.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
