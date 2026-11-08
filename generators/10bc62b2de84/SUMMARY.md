# 10bc62b2de84

0-bg grid (h ∈ 6-14, w ∈ 10-22, by difficulty) with: N_OBJECTS ∈ 2-6 4-CONNECTED COLORED BLOBS, each in a DISTINCT color drawn from {1..9}, each of size 2-7 cells built via _grow_blob random walk, placed at non-overlapping positions with 1-cell padding via bbox-conflict check. Each blob has a unique left-edge column. Rule (SORT OBJECTS BY THEIR LEFTMOST COLUMN (OBJ-C1) ASCENDING; CROP EACH OBJECT TO ITS BBOX; HORIZONTALLY PACK THE BBOX CROPS LEFT-TO-RIGHT WITH 1-CELL 0-GAPS BETWEEN, BOTTOM-ALIGNED WITHIN OUTPUT HEIGHT = MAX BBOX HEIGHT): EXTRACT every 4-connected component with bbox. SORT by leftmost column. CROP each to its bbox (preserving the original color). COMPUTE out_h = max bbox height. BUILD output of size out_h × (sum_widths + (n-1) gaps). For each sorted object: PASTE its bbox crop at current x-offset with top = out_h - bbox_h (bottom-aligned). Net: scattered objects collected and packed left-to-right, bottom-aligned, with single-cell gaps between.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
