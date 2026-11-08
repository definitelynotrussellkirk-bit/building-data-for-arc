# 19a48004b265

Multicolor grid (h, w ∈ 2-18, by difficulty), palette of 2-9 distinct colors drawn at random (may include 0), filled by TEXTURE ∈ {noise / sparse / blob / stripes / gradient / checkerboard / frame / ring / plus} via fill_texture. After base fill: (a) apply_bg_density (0-50%) introduces bg sparsity; (b) apply_noise_overlay (0-10%) flips random cells; (c) apply_border per BORDER_MODE ∈ {free, always_bg, always_fg} may overwrite the outer border. The grid is GENERALLY NOT TRANSPOSE-SYMMETRIC (rectangular or asymmetric content), so the rule has visible effect. Rule (TRANSPOSE THE GRID — SWAP ROWS AND COLUMNS): OUTPUT[c][r] = INPUT[r][c] for all (r, c). Result is a w×h grid where the input's rows become the output's columns and vice versa. Net: the entire grid is reflected across the main diagonal — each cell value moves to its transposed position.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
