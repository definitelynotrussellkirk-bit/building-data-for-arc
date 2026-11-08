# 1c781334a4f3

0-bg grid (h~9-11, w~11-13) with 3-4 connected MOTIFS at distinct non-touching positions, each in a DISTINCT color from {2..9} and each of size 3-5 cells. Motifs have 1-cell padding from each other and grid edges. Rule (VERTICAL GALLERY PACK): identify each MOTIF as a connected component. CROP each motif to its BBOX. STACK the cropped motifs VERTICALLY in canonical order. Output WIDTH = MAX bbox width; HEIGHT = SUM of bbox heights. Net: scattered motifs → vertical gallery.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
