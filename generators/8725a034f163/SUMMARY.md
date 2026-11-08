# 8725a034f163

Multicolor grid (h, w ∈ 2-6, by difficulty), palette of 2-6 distinct colors drawn at random, filled by dense TEXTURE ∈ {noise / stripes / gradient / checkerboard} via fill_texture. After base fill: apply_bg_density (0-40%) adds sparsity; apply_noise_overlay (0-5%) flips cells. ≥2 distinct colors guaranteed (if monochrome after all transforms, force corners to different palette colors). Rule (4-FOLD KALEIDOSCOPE — OUTPUT IS 2H × 2W WITH 4 QUADRANTS: TOP-LEFT = INPUT, TOP-RIGHT = LR-MIRROR OF INPUT, BOTTOM-LEFT = UD-MIRROR OF INPUT, BOTTOM-RIGHT = 180°-ROTATION OF INPUT): For an h×w input g, BUILD output of size (2h) × (2w). For positions (r, c): TOP-LEFT (r < h, c < w) = g[r][c]; TOP-RIGHT (r < h, c ≥ w) = g[r][2w-1-c]; BOTTOM-LEFT (r ≥ h, c < w) = g[2h-1-r][c]; BOTTOM-RIGHT (r ≥ h, c ≥ w) = g[2h-1-r][2w-1-c]. Net: input is reflected into a 4-quadrant symmetric pattern.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
