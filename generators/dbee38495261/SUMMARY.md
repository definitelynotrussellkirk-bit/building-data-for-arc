# dbee38495261

A color-1 wall maze contains one start marker 2, one end marker 3, and one to four distinct intermediate markers chosen from 4..7. Visit present intermediate markers in ascending color order between 2 and 3. For each leg, run deterministic four-neighbor BFS through non-wall cells using neighbor order up, down, left, right. Paint only traversed color-0 cells with color 8; preserve walls and all markers.

The v3.0.0 generator constructs connected mazes and accepts only scenes that distinguish the selected rule from wall-ignoring, direct start-to-end, reverse waypoint order, and row-major waypoint-order shortcuts when applicable. Its exact axes are `grid_h` 7..14, `grid_w` 9..16, and `n_mids` 1..4. A four-example schedule covers all midpoint counts and includes a canonical-size profile.

Kind: `per_puzzle`. Version: `3.0.0`. Canonical rule hash: `f1fa88aeec11`.
