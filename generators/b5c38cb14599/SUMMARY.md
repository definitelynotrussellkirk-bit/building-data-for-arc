# b5c38cb14599

0-bg grid (h~8-10, w~11-13) with: (a) cell (0,0) = an OP KEY value in {1, 2, 3}; (b) one connected color-4 (yellow) motif (3-5 cells); (c) one connected color-6 (magenta) motif (3-5 cells). Both motifs placed apart from each other and from (0,0). Rule: read key = grid[0][0]. Take largest color-4 component → mask-crop to its bbox (1=cell, 0=bg). Same for color-6 → mask b. Pad both to max(h_a, h_b) × max(w_a, w_b) at top-left. For each cell: key=1 → cell non-zero in EITHER (UNION); key=2 → non-zero in BOTH (INTERSECTION); else → non-zero in exactly ONE (XOR / symmetric difference). Paint result cells color 8 (cyan). Output: crop to content.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
