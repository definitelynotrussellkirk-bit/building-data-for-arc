# 0f26224a6da3 — generator 3.0.0

Zero-background integer-color grids, helpful dimensions 7..15, containing exactly 2..5 four-neighbor-isolated active cells. The unchanged rule extends each active cell one cardinal step in its own color, clips at boundaries, preserves centers and all existing foreground, and leaves cardinally connected cells inert. Isolation is evaluated on the original input.

Helpful generation cycles interior, boundary-plus-domino, and diagonal-pair-plus-domino scenes by `(seed + sample_index) % 3`. Interior defaults are 7..9; other scenes are 7..15. A diagonal same-color pair distinguishes four-neighbor from eight-neighbor isolation without ambiguous cross-color overwrites. Other source placements use arbitrary coordinates with spacing, not a modulo-three lattice. There is at most one inert domino. Different-color competing expansion targets are excluded from helpful training data.

Default active counts: easy 2..3, medium/unspecified 2..4, hard 3..5. Exact overrides: grid_h, grid_w, n_cells; palette_kind selects warm/cool/broad/primary; texture aliases those palettes; scene chooses the profile. Unknown or invalid controls raise errors. Explicit diagnostic textures no_cells/full_cells/full_grid are outside the helpful domain and fail self_check. Colors are sampled from the chosen palette, not cycled by index.

At fixed seed, any three consecutive unoverridden demonstrations refute the three declared rivals. This does not cover arbitrary filtering, shuffling, or fewer demonstrations. Run the workspace post-assembly gate on actual labeled lessons. It checks a finite rival family, not universal identifiability; upstream labels still come from Racket.

Review assignment: review-82548b4b24894693. Rule hash: 867443694c3b, unchanged. No training approval is claimed; approval is derived by the catalog from current code and independently retained evidence. See notes.md and workspace/README.md for tests, reproducibility, and known limitations.
