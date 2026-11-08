# 5cff884f1d16

Colored grid (h~2-12, w~2-15) drawn with one of 9 TEXTURE patterns (noise/sparse/blob/stripes/gradient/checkerboard/frame/ring/plus) from a palette of 2-6 colors with bg_density 0..0.4 and noise_overlay 0..0.05. The grid is guaranteed NOT UD-SYMMETRIC (forced asymmetric: g[0][0] is perturbed if needed) and has ≥2 distinct colors. Rule (VCONCAT INPUT + UD-MIRROR): EMIT a (2h)×w OUTPUT GRID where TOP HALF (rows 0..h-1) = INPUT, and BOTTOM HALF (rows h..2h-1) = FLIP_UD(INPUT) — i.e., row h+k of output = row h-1-k of input. The shared edge (row h-1 vs row h) is the mirror axis. Net: input is reflected downward; output is input stacked above its vertical mirror image.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
