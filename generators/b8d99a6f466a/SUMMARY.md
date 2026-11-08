# b8d99a6f466a

0-bg grid (h, w ~8-12) with color-1 (blue) WALLS splitting the canvas into 2 (horizontal split at row h//2) or 4 (cross split at row h//2 and col w//2) ROOMS. Each room contains exactly one MARKER cell in a distinct non-{0, 1} color at a random interior position. Rule: detect color-1 walls dividing the grid. For each ROOM (connected bg region bounded by walls), find its marker color. FLOOD the room (every bg cell of that room) with the marker's color. Walls stay color 1.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
