# a2e841db66ad

0-bg grid (h×w, ~10-22 by ~11-22) with row 0 acting as HEADER: exactly k color-1 (blue) cells at the leftmost columns (k=1..5). Body (rows 1..h-1) contains 3-5 connected components in distinct non-zero non-1 colors. EXACTLY ONE component has bbox-height k; other components have different bbox-heights (distinct from k). Rule: read k = count of color-1 cells in row 0. Extract body = rows 1..h-1. Find first component (in top-left order) whose bbox-height equals k. Crop to its bbox, recolor all non-zero cells to color 8 (cyan). Output = the cropped+recolored component.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
