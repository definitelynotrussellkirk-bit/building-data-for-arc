# 82b36c453029

0-bg grid (h×w, ~8-11 by ~9-13) with 3-5 isolated solid-filled RECTANGLES in distinct non-zero colors. Rectangles have area > 1 (so bbox center collapse is non-trivial). Each rectangle is rh × rw (rh = 1-3, rw = 2-4 or 1-4). Rectangles are separated by ≥1-cell buffer (8-conn isolated). Rule: build fresh 0-canvas. For each connected component, compute bbox center (mid_r, mid_c) = ((r1+r2)//2, (c1+c2)//2). Paint that single cell with the component's color. Output: same dimensions; only the computed center cells are non-zero.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
