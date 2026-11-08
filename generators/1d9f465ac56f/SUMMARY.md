# 1d9f465ac56f

0-bg grid containing 3-5 connected motifs in distinct non-zero colors, placed with ≥1-cell buffer between them. EXACTLY ONE target motif satisfies all three properties: (a) its bbox is SQUARE (h==w); (b) its binary mask is symmetric along the main diagonal (mask[r][c] == mask[c][r]); (c) it contains ≥1 HOLE (at least one bg cell strictly inside the bbox, not on the outline). Other motifs (decoys) fail at least one of these properties. Rule: find the unique target. Crop it. Recolor all non-zero cells to color 8. Upscale ×2 (each cell → 2×2 block). Output size = 2*target_bbox_side per side.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
