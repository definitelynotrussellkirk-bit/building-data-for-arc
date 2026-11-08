# 57a3b93dd3e0

0-bg grid (size varies) with: (a) a color-1 MARKER in the top-left 2x2 (its position encodes a rotation k: (0,0)->0, (0,1)->1, (1,1)->2, (1,0)->3); (b) one connected color-2 STENCIL (3-6 cells); (c) one SINGLE color-4 ANCHOR cell. Rule: rotate the stencil's normalized cells by k and paint them in color 8 onto a fresh blank grid at the anchor position. Output dims = input dims; only the rotated stamp (color 8) is drawn.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
