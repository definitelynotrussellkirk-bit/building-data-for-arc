# 24a7dc5a6db9

Sparse color-2 (red) cells on a 0-bg grid (with optional distractor cells in other colors). Rule computes the bbox of the red cells, then paints color 8 onto every border-of-bbox position (row=r0 or r1, or col=c0 or c1) that is currently 0. Existing reds on the border stay 2. Cells inside the bbox interior stay unchanged. Cells outside the bbox stay unchanged.

Kind: `per_puzzle`. Imported version: `1.2.1`.
Approval is derived by the catalog from current code and retained evidence.
