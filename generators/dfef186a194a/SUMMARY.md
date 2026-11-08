# dfef186a194a

Color-1 (blue) background grid (~12-22 per side) with non-bg OBJECTS arranged in a regular N×M GRID LAYOUT (N, M = 3..5 each). All objects share a single non-1 color, each 1-2 cells, separated by ≥1 cell of bg. Rule: detect all non-bg objects (bg=1). Determine each object's row-index ri (in sorted unique top-rows) and column-index ci (in sorted unique left-cols). If object is on the BORDER of the layout (ri == 0 OR ri == N-1 OR ci == 0 OR ci == M-1), recolor its cells to color 2 (red). Otherwise (interior of layout), recolor to color 3 (green). Background stays 1.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
