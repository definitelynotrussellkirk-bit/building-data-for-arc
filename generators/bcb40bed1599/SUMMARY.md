# bcb40bed1599

0-bg grid (h~4-6, w~8-10) with: (a) the RIGHTMOST column filled entirely with color-9 (maroon) cells — the DOCK; (b) one connected BLOB of 3-4 cells in some non-{0,9} color, placed on the LEFT side with empty space to its right. Rule: extract dock cells and blob cells. While the blob can be shifted east by 1 (all next-column cells in bounds AND either 0 or in the blob itself), shift it east. Stop when shifting would hit the dock or wall. Output: empty grid + dock(9) + blob in original color at final position (abutting the dock).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
