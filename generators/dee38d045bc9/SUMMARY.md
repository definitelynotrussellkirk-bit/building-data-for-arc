# dee38d045bc9

A 0-background grid contains two or three X-shaped motifs. For each blank interior cell, inspect its four diagonal neighbors. If all four are nonzero and have the same color, fill the blank center with that color; otherwise leave it unchanged. All source pixels are preserved and updates are non-cascading.

Ordinary generated scenes include one disjoint negative control: three matching diagonals and one blank, four nonzero diagonals with unequal colors, or four matching diagonals around an already nonzero center. Positive motifs may share one color or use distinct colors, and a sparse opposite orthogonal context pair sometimes appears around a valid center. These branches distinguish the rule from color-count, one-center-per-color, partial-X, mismatched-X, overwrite, blank-orthogonal, and texture-conditioned shortcuts.

Exact controls: `grid_h=7..17`, `grid_w=7..17`, `cross_count=2..3`, `color_mode=distinct|shared`, and `texture=mismatched_diagonals|partial_diagonals|blocked_center`.

Kind: `per_puzzle`. Version: `3.0.0`. Rule hash: `3de95ecac741`. Demonstrations required: `5`.
Approval is derived by the catalog from current code and retained evidence.
