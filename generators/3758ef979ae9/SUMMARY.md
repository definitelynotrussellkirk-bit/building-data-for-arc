# 3758ef979ae9

Grid is a 2×2 grid of rectangular ROOMS separated by color-1 (blue) WALLS (also color 7 and 9 count as walls in the rule). Each room has bg=0 floor with at most one non-wall non-bg single-cell SEED at the room's center. Rule: extract the rooms (BFS over non-wall cells). For each room, find its seed (any non-bg, non-wall cell). If a seed exists, flood-fill the room's floor cells with that seed's color. Empty rooms stay 0. Walls remain unchanged.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
