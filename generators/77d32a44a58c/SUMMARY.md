# 77d32a44a58c

0-bg grid (h~8-12, w~8-13) with: (a) CELL (0, 0) is the TARGET COLOR LEGEND in some color from {1..9}; (b) ONE NON-LEGEND OBJECT in the TARGET COLOR — drawn from a 4-shape bank (4-5 cell shapes), placed at an interior position with 1-cell padding; (c) 1-4 DISTRACTOR OBJECTS in DISTINCT non-target colors at scattered positions. Output uniq_out=23 (intrinsic — 4 shape banks × ~9 colors normalizes). Rule (CROP LEGEND-COLOR OBJECT): READ TARGET COLOR T = g[0][0]. Identify the BODY OBJECT in color T (excluding the (0, 0) legend cell itself). CROP that object to its BBOX. EMIT the cropped subgrid. Net: (0, 0) color points to the matching body object; output is its tight crop.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
