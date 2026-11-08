# 26cfe7595a4a

0-bg grid (h~6-10, w~7-11) with ONE COMPACT MULTICOLOR MOTIF placed in the interior (rows 1..h-mh-1, cols 1..w-mw-1) where mh, mw ∈ 2..4. Motif is filled at 70% density with 3 DISTINCT colors arranged in a checker (color[(r+c) % 3]). Bbox corners of the motif are guaranteed non-zero so bbox is well-defined. Surrounding bg padding ≥1 cell on all sides. Rule (TIGHT BBOX CROP): identify all non-0 cells. COMPUTE their BBOX. CROP the grid to that BBOX. EMIT the cropped subgrid. Net: surrounding bg padding is removed; output is the tight motif crop.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
