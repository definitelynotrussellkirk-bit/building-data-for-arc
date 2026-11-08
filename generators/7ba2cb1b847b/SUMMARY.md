# 7ba2cb1b847b

0-bg grid (h, w~8-15) with 1-2 CLOSED FRAMES of varied kinds: rect_outline / blob_outline / irregular_polygon / U_shape / nested_rects, drawn in a WALL_COLOR (random non-{0, 1}) of varying sizes (3-5 small, 5-h-4 medium, h//2-h-4 large, or mixed). Each frame is closed (its interior 0-region isn't connected to the outer border). Optional inner wall-color marker cell with probability 0..0.7. Optional 0..0.05 density of decoy non-{0, 1, wall} cells outside frames. Rule (FILL ALL ENCLOSED 0 REGIONS WITH COLOR 1): for EACH 0-CELL, check if it's ENCLOSED by non-0 walls (NOT reachable from the grid border through 0-cells). If enclosed, RECOLOR to COLOR 1 (blue). Open frames (interior touches border) and outer 0-cells stay 0. Inner markers stay. Walls stay. Net: closed-frame interiors fill with blue.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
