# 2dae2c34641b

Version 2.0.0 generator for vertical-then-horizontal elbow paths.

A lawful input contains two or three nonzero colors, each appearing at exactly two endpoints on distinct rows and columns. For each color, the upper endpoint connects vertically to the lower row, then horizontally to the lower endpoint. Generated authoritative paths are pairwise disjoint.

Exact controls: `grid_h`, `grid_w`, `n_pairs`, `palette_kind`, and `bend_pattern`. Three consecutive default samples teach left, right, mixed, and three-pair cases. The canonical Racket rule hash is pinned as `95bc32a62544`.
