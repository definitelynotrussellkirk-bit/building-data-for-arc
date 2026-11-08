# f35919cb93b9

0-bg grid (h×w, ~9-12 by ~9-12) with: (a) EXACTLY ONE color-9 PIVOT cell placed roughly in the center; (b) a SOURCE shape of 1-3 non-{0, 9} cells in some single color, placed off-center so its 4 rotations land at distinct positions and stay in bounds. Rule: find pivot. For each non-zero non-9 cell at (r, c), compute offset from pivot. Generate 4 rotational offsets (90° turns: (dr, dc), (dc, -dr), (-dr, -dc), (-dc, dr)). Paint each rotated position with the cell's color (if in bounds). Output: input + 3 rotated copies of each source cell.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
