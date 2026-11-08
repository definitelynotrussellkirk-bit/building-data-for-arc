# edac81ec2559

0-bg grid (h~7-9, w~7-10) with 4-7 scattered MARK CELLS placed in the UPPER HALF (rows 0..h//2-1, excluding cells on the exact midline if h is odd) in various non-zero colors from {1..9}. The LOWER HALF (rows h//2..h-1) and the midline (if odd h) are entirely BACKGROUND. Rule: REFLECT the grid across the HORIZONTAL MIDLINE — for every cell (r, c) with a non-zero value v, also paint cell (h-1-r, c) with v (its mirror across the horizontal axis). Original upper-half cells STAY in place. If the midline row exists (odd h), it stays. Net: input is upper-half marks; output is the same marks ALSO appearing reflected in the lower half, creating a vertically symmetric pattern.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
