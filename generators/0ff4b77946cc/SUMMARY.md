# 0ff4b77946cc

0-bg grid (h ∈ 8-16, w ∈ 11-18, by difficulty) with: N_SHAPES ∈ 3-4 OBJECTS drawn from _SHAPES bank (6 variants of sizes 1, 3, 4, 5, 8, 9 — single cell, L, T-pentomino, ring 3×3, solid 3×3), each with a DISTINCT SIZE drawn WITHOUT REPLACEMENT, each painted in a DISTINCT color from {1..9}, placed via place_no_overlap with 1-cell padding. Total packed width fits within w. Rule (SORT OBJECTS BY (SIZE DESC, BBOX-H ASC, BBOX-W ASC, COLOR ASC); PACK THEM HORIZONTALLY FROM THE LEFT WITH 1-COL BG GAPS, PRESERVING EACH OBJECT'S ORIGINAL SHAPE AND COLOR): EXTRACT every non-bg component. SORT by tuple (-cell_count, bbox_h, bbox_w, color). CROP each to its bbox. PACK left-to-right with 1-COLUMN BG GAPS between, TOP-ALIGNED. Output height = max bbox height across all objects; width = sum_widths + (n-1). Net: largest objects go first, left-aligned packing yields a sorted gallery.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
