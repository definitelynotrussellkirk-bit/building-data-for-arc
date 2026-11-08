# 14dacb3b518f

A color-0 grid contains 1–2 separated **holed** color-6 components and 1–2 separated **hole-free** color-6 components. For each 4-connected color-6 component, count background regions enclosed inside its bounding box:

- at least one enclosed hole → recolor the entire component **8**;
- no enclosed hole → recolor the entire component **2**;
- keep background cells **0**.

The five-profile curriculum includes thin frames, filled pockets with an enclosed cavity, a connected two-hole object, leaky C-shaped near-misses, small ordinary solids, and a hole-free rectangle larger than every holed object. These cases refute the canonical shortcuts “thin rectangular frame,” “size ≥ 8,” “exactly one hole,” “two largest components,” and the broader rival “any bounding-box gap.”

Exact observable controls: `grid_h=10..14`, `grid_w=12..16`, `n_holed=1..2`, and `n_solid=1..2`. Placement uses four separated slots, so requested object counts are constructive rather than best-effort rejection sampling.

Kind: `per_puzzle`. Version: `3.0.0`. Pinned authority: `RULE_HASH = fe78a969401a`.
