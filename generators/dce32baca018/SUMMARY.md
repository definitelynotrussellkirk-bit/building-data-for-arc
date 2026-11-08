# dce32baca018

0-bg grid (h~5-7, w~7-9, w should be ODD for a centered divider) with: (a) FULL-HEIGHT COLOR-5 DIVIDER at col w//2 — every row of col w//2 painted gray; (b) LEFT BLOB — 2-4 CELLS in a single non-{0, 5} color placed at random positions on the LEFT side (cols 0..w//2-1) where the mirrored target on the right stays in bounds; (c) RIGHT SIDE (cols w//2+1..w-1) is INPUT-EMPTY. Rule (MIRROR LEFT BLOB CELLS ACROSS THE GRAY DIVIDER TO THE RIGHT): identify the FULL-COLUMN GRAY (5) DIVIDER at col div. For EACH NON-0 NON-5 CELL at (r, c) with c < div: PAINT (r, 2*div - c) on the RIGHT with the SAME COLOR. Divider and original cells stay. Net: left blob appears mirrored across the gray divider on the right side.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
