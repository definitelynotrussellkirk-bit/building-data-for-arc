# af6e765bcc41

0-bg grid (h, w ∈ 10-14) with: N_FRAMES ∈ 1-3 HOLLOW COLOR-7 (ORANGE) RECTANGULAR FRAMES, each rh × rw (rh, rw ∈ 4-6) drawn via draw_rect_outline at non-overlapping interior positions (1-cell padding between frames via bbox-distance check). Each frame's INTERIOR (cells strictly inside the outline) starts EMPTY (color 0). Rule (FOR EACH HOLLOW ORANGE FRAME, FILL ITS INTERIOR WITH COLOR 8 (CYAN); FRAME OUTLINE STAYS ORANGE): IDENTIFY every 4-connected COLOR-7 component. For EACH frame: COMPUTE its bbox (rmin, cmin, rmax, cmax). For EVERY (r, c) with rmin < r < rmax AND cmin < c < cmax (strictly interior): IF g[r][c] == 0: PAINT g[r][c] = COLOR 8 (cyan). The frame outline (7s) stays 7. Cells outside any frame stay 0. Net: each orange frame's hollow center fills with cyan, turning frames into orange-bordered cyan blocks.

Kind: `per_puzzle`. Imported version: `2.0.3`.
Approval is derived by the catalog from current code and retained evidence.
