# 83e70bd8c0a1 — full anti-diagonal reflection

Reflect every cell of a square grid across the anti-diagonal:
`output[r][c] = input[n - 1 - c][n - 1 - r]`. Anti-diagonal cells are fixed;
all other cells move to their paired position. The Racket authority is unchanged
and pinned by `RULE_HASH = "ea62a41435bf"`.

Generator version `3.0.0` draws 5×5–7×7 grids with exactly six foreground
colors. Every ordinary draw contains 1–3 occupied anti-diagonal fixed points,
1–2 differently colored occupied mirror pairs, 4–5 singleton mirror orbits, a
corner axis witness, and a repeated moving color. These structures distinguish
the full transform from copy/overlay, erase-fixed-point, preserve-collision,
unique-color-only, and main-diagonal shortcuts.

Exact controls are `grid_size`, `diagonal_marks`, `mirror_pairs`, and
`singletons`; `observe_overrides()` recovers all four from the returned grid.
`self_check()` accepts every canonical input and enforces the owned six-color
sparse manifold. Task-local tests and `workspace/qualify_distribution.py`
exercise canonical support, invalid calls, joint control support, semantic
rivals, and every cyclic query rotation.

Kind: `per_puzzle`. Imported version: `2.0.1`; repaired version: `3.0.0`.
Approval remains a catalog/maintainer decision derived from current source and
retained evidence.
