# 022240cb671b

0-bg grid (h, w~8-16) with 1-3 small RECTANGULAR OBJECTS (1×1 up to ~h/4 × w/4) painted in distinct non-zero colors from a palette of 2-5 colors. Objects are placed at INTERIOR positions with 1-cell margin from the grid edges and from each other, so the non-bg content's bbox is strictly smaller than the input grid (the grid is padded with bg). Rule: COMPUTE the BOUNDING BOX of all NON-BG cells (rmin..rmax × cmin..cmax). CROP the grid to exactly that bbox — output is the rectangular subgrid containing only the content, with all bg padding outside the bbox stripped away. Net: input is padded; output is the tight bbox crop of the content (smaller dimensions).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
