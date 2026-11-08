# 75837d4fa905 — Square Corner Bloom

A zero-background grid contains two to four distinct-colour solid monochrome
2×2 squares.  For each square, copy its colour to the four diagonal cells one
step beyond the square: `(r-1,c-1)`, `(r-1,c+2)`, `(r+2,c-1)`, and
`(r+2,c+2)`.  Keep the square unchanged, clip targets outside the grid, and
only paint cells that are still background; therefore the first source visited
in row-major order wins a shared target.

Generator version: `3.0.0`.  Exact public controls are `grid_h` 7–16,
`grid_w` 8–18, and `n_squares` 2–4.  Default four-pair lesson windows use
three demonstrations plus one query and guarantee two boundary-clipped
witnesses, so every allowed query rotation still refutes the canonical-fitting
`interior_only` shortcut.

The canonical Racket authority is unchanged and pinned by `RULE_HASH =
"e56cca9b3b6c"`.
