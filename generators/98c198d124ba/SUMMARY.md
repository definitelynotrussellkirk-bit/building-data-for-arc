# 98c198d124ba

0-bg grid with 2-4 hollow rectangular FRAMES in distinct non-zero colors. Each frame is ≥3×3 (so it has an interior). Frame interiors are bg (0), forming HOLE REGIONS enclosed by the frame color. Frames don't overlap or touch. Rule: find all 0-regions (connected groups) that are ENCLOSED (not reachable from grid border through 0-cells). For each enclosed region, find its adjacent frame color. Build a small grid showing the region cells in that color. Sort regions by (size DESC, height ASC, width ASC). Pack the grids horizontally bottom-aligned with 1-col gap. Output is the packed gallery.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
