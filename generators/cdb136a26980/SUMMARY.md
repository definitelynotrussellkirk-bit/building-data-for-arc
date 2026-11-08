# cdb136a26980

0-bg grid (h~6-9, w~9-13) with 2-4 ACTIVE ROWS, each containing: (a) ONE COLOR-9 (maroon) ANCHOR cell at column p (3..w-3); (b) 1-3 COLORED MARKER cells on the LEFT side of the anchor (cols max(0, p-3) to p-1) in random colors from {1..8}. Non-active rows are 0. Rule (MIRROR LEFT-SIDE MARKERS ACROSS 9-ANCHOR): For EACH ROW r containing a COLOR-9 ANCHOR at col p: For EACH non-0 non-9 cell at (r, c) with c < p, PAINT the MIRROR position (r, 2p - c) with the same color (if in-bounds). The anchor stays. Source cells stay. Net: each row with a 9-anchor reflects its left-side markers to the right side.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
