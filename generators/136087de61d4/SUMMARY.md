# 136087de61d4

0-bg grid (h×w, ~8-10 by ~11-14) with exactly TWO color-3 (green) endpoint cells and several color-9 (maroon) WALL cells forming partial barriers (e.g., 2-3 vertical walls with single-cell gaps). Endpoints placed at distant corners so the shortest path must detour around walls. Rule: locate the two color-3 cells. Run 4-connected BFS treating 0-cells as walkable and 9-cells as walls. Find the shortest path between the endpoints. Paint all INTERIOR cells of the path (excluding the two endpoints) with color 8 on top of the input. Walls and endpoints preserved. Output color set: {0, 3, 8, 9}.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
