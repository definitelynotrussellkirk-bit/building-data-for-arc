# 63a780e1d475

A zero-background grid contains blue (`1`) endpoint pairs aligned in rows, columns, or both. For each pair of **consecutive** blue cells in the same row or column, when at least one cell lies between them and the complete interior is zero in the original input, recolor the entire inclusive span—including both endpoints—red (`2`). All eligibility tests use the unchanged input, so crossing horizontal and vertical spans are both painted.

The generator produces 8–14 by 9–14 grids with 2–4 disjoint endpoint pairs. Its exact controls are `grid_h`, `grid_w`, `n_pairs`, and `orientation_mode` (`horizontal_only`, `vertical_only`, `mixed_clear`, or `mixed_crossing`). The default ordered curriculum anchors all five canonical shapes, includes single-orientation and crossing cases, and varies pair count by difficulty.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical rule hash: `b3ad5e9b6be9`.
Approval is derived by the catalog from current code and retained evidence.
