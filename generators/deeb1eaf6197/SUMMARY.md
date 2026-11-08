# deeb1eaf6197

0-bg grid (h 10..19, w 12..22) with 2-4 4-connected same-color components, each a distinct color (different-colored components may touch edge-to-edge, as in canonical train pair 2; their bboxes never overlap). Each component is one of: solid rect (0 holes), open/notched rect (0 holes but zeros inside the crop touch the crop border), ring (1 enclosed hole), or double-ring (2 enclosed holes). Rule: crop each component to its bbox, count ENCLOSED interior 0-regions, sort by (hole_count asc, reading-order index asc), and pack the crops LEFT-TO-RIGHT with one blank column between consecutive crops. Output height = max crop height; width = sum of crop widths + (n-1) gap columns.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
