# fc68d333e854

0-bg grid (size varies). Several ACTIVE rows each contain exactly one color-9 AXIS marker plus 1-5 other colored cells (colors 1-8) placed on EITHER side of the axis; each such cell has an in-bounds, currently-empty MIRROR slot across the axis. Some grids also include DECOY rows that hold stray colored cells but NO 9 axis. Rule: for each row, find the LEFTMOST 9 (the axis). For every non-0/non-9 cell in that row, copy it to its mirror column (2*axis - c) when that destination is in-bounds and still empty. Rows without a 9 are left unchanged. Net: every axis row becomes left-right symmetric about its 9; decoy rows pass through untouched. (Was tiny grids, 2-3 rows, cells on one side only, near-fixed colors.)

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
