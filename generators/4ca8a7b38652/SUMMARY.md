# 4ca8a7b38652

Small FULLY COLORED grid (h, w~2-5) where every cell is non-bg (no 0s). The grid contains n_colors distinct non-bg colors (n_colors ∈ [2..9]), with n_colors * max(h, w) ≤ 30 so the upscaled output fits ARC's 30×30 limit. Cells are filled with one of several texture patterns (noise, sparse, blob, stripes, gradient, checkerboard, frame, ring, plus). Rule: COUNT the number of DISTINCT colors n in the input grid. UPSCALE the grid by factor n: each cell (r, c) becomes an n × n block of the same color. Output dimensions: (n*h) × (n*w). Net: a small multi-colored grid is replicated at scale n where n is its own color-count.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
