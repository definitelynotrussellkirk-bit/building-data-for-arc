# fd9fa5d1f8a3

0-bg grid with 2-12 ISOLATED SINGLETON cells in varied non-zero colors, placed ANYWHERE (interior OR on the edges/corners) with a 2-cell buffer between any pair so radius-1 plus expansions never overlap. Rule: produce a FRESH same-size empty grid; for each non-zero source cell at (r, c), paint a plus — the cell itself + its 4 cardinal neighbors — in the same color, keeping only in-bounds cells (edge/corner pluses are clipped). Net: each singleton expands into a radius-1 plus of its color.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
