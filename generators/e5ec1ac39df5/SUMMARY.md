# e5ec1ac39df5

Grid laid out as a 2×2 grid of ROOMS separated by 1-wide WALLS (color 1) plus an outer wall frame. Each room is a rectangular 3-5 × 3-5 0-bg interior. 1-2 rooms have a SEED cell at their center in color 2 (red). Rule: detect the room-graph (rectangular regions separated by walls). For each room that CONTAINS a color-2 cell, collect its WALL-BOUNDARY CELLS (the wall cells immediately adjacent to that room's interior). Output: a fresh empty grid of the same shape, with those wall cells painted 8 (cyan), everything else 0. Non-seeded rooms' walls stay 0.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
