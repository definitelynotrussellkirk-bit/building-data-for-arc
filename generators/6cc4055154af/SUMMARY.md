# 6cc4055154af

0-bg grid (h~8-10, w~8-11) with: (a) ONE BORDER-TOUCHING COMPONENT placed flush against one of the 4 grid edges in some random non-zero color; (b) 2-3 INTERIOR COMPONENTS placed strictly inside (rows 1..h-2, cols 1..w-2, with 1-cell padding from each other) in distinct non-zero colors. All components are small polyominoes (2-3 cells from a shape bank: L-tromino, S-tromino, line, domino). Rule: identify each CONNECTED COMPONENT. For EACH component, check if it has ANY cell ON the GRID BORDER. DROP (clear to 0) every border-touching component. KEEP (preserve) every strictly-interior component at its original color. Net: border-touching blobs erased; interior blobs survive.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
