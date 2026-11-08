# 185447d509d8

Four isolated, differently coloured tetrominoes are ordered by the row-major positions of their bounding boxes. The output is a 4×4 matrix: cell `[i][j]` is red (`2`) exactly when objects `i` and `j` have the same binary shape under any of the eight dihedral symmetries (four rotations and four reflected rotations); otherwise it is black (`0`).

Generator version: `3.1.0`. Canonical rule hash: `9586787e3555`.

Exact controls:

- `size_profile`: `12x14`, `13x15`, `12x16`, `14x14`, or `12x15`;
- `partition`: `one_pair` or `two_pairs`.

Every ordinary input contains a reflection-only equivalent pair and equal-area non-equivalent shapes, so rotations-only, exact-orientation-only, and same-area shortcuts are contradicted. Easy/medium/hard bands alter visible size and partition schedules while preserving the same rule.

Kind: `per_puzzle`. Approval remains catalog-derived from current code and retained evidence.
