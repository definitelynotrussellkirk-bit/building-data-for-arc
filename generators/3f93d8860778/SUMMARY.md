# 3f93d8860778

On a zero-background 7..12 by 8..11 grid, 2..5 columns contain exactly two matching coloured endpoints separated by at least one zero. Fill only each such inclusive vertical interval. Columns containing a singleton, two different colours, or a gapped same-colour triple remain unchanged.

Training uses a deterministic three-example curriculum: one clean canonical-like scene and two independently drawn complete guard scenes. Every guard contains all three non-firing patterns, repeats one valid-pair colour, and retains another valid-pair colour, so plausible global-count, all-active-column, extrema and one-colour shortcuts are directly contradicted even under query rotation. Sparse default slots reproduce observed canonical height/width/palette profiles; public exact axes remain `grid_h`, `grid_w`, and `spans`.

Kind: `per_puzzle`. Selected version: `4.0.0`. Canonical authority unchanged; pinned rule hash `abdf780ecbe7`.
