# fd93f1d51f8b

0-bg grid (h ∈ 8-10, w ∈ 9-12) with: ONE SMALL MOTIF of DIMENSIONS mh × mw (mh ∈ 2-4, mw ∈ 2-5) embedded at a random INTERIOR position (top ∈ 1..h-mh-1, left ∈ 1..w-mw-1) with ≥1-CELL MARGIN of 0s all around. The motif's CORNER CELLS (0,0) and (mh-1, mw-1) are always painted (so the bbox is well-defined). Additional interior cells of the motif painted randomly in 1-3 DISTINCT non-bg colors drawn from {1..9}. Some motif interior cells may stay 0. Rule (CROP THE GRID TO THE MINIMAL BOUNDING BOX CONTAINING ALL NON-BG CELLS): COMPUTE the BOUNDING BOX of all non-bg cells (rmin, cmin, rmax, cmax). EXTRACT the subgrid g[rmin..rmax][cmin..cmax]. OUTPUT this cropped subgrid. Net: the surrounding 0-border is stripped; only the embedded motif remains, preserving its internal pattern.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
