# a950d6dbe2e0 — Four-Quadrant Symmetry

Version 2.0.0 generates multicolour motifs in the upper-left quadrant of even
4..30 by 4..30 canvases. The selected canonical Racket authority, hash
`6c2ec896ad53`, copies each seed across both full-grid midlines; it is unchanged.

Exact observable controls are `grid_h`, `grid_w`, `n_cells` (2..64), and
`n_distinct_colors` (2..9). Infeasible combinations raise structured errors.
Every chosen colour appears. All positions within the source quadrant remain
available, including border and midline-adjacent cells.

Default indices repeat square/rectangle/rectangle. Square draws preserve
8x8, 10x10 and 12x12 canonical profiles; positions and colour identities are
newly sampled. The three-demo curriculum distinguishes height-for-both-axes
and width-for-both-axes shortcuts, which fit all three canonical pairs.
Explicit controls override this default lesson schedule.

The training domain intentionally excludes monochrome, empty, odd-dimensional,
and exterior-seed inputs. These are domain limits, not claims that the Racket
rule is undefined there. Five legacy inert controls were retired and now fail
visibly; see notes.md. Approval remains a maintainer action bound to source bytes.
