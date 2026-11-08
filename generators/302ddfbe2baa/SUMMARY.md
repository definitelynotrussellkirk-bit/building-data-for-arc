# 302ddfbe2baa — Rightward Ray Paint

Yellow (4) emitters paint cyan (8) into zero cells to their right. A ray preserves and passes through other non-maroon colors, stops immediately before the first maroon (9), and otherwise reaches the edge.

Kind: `per_puzzle`. Generator version: `2.0.0`. Canonical rule hash: `923c6879d312`.

The three-example curriculum cycles through:

1. a canonical anchor;
2. a pass-through distractor witness;
3. a multi-blocker/direction witness.

Every consecutive three-example window refutes the declared canonical-fitting shortcuts `stop_at_any_nonzero`, `rightmost_maroon`, `toward_nearest_maroon`, and `first_three_emitters`.

Exact axes: `grid_h` (6–10), `grid_w` (10–14), `emitter_count` (1–5), and `scene_kind` (`canonical|pass_through_distractor|multi_blocker`).

Approval remains catalog-derived from current code and retained evidence.
