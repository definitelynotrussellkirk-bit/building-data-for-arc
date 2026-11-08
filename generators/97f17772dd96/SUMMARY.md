# 97f17772dd96

0-bg grid (h~9-12, w~9-12) with TWO NESTED COLOR-1 RECTANGULAR FRAMES: (a) OUTER FRAME — rectangular outline from (1, 1) to (h-2, w-2) painted in color 1 (border-only rectangle, interior cells stay 0); (b) INNER FRAME — rectangular outline from (3, 3) to (max(3, h-6), max(3, w-6)) also painted in color 1, nested strictly inside the outer frame. The two frames define DEPTHS: cells outside any frame have depth 0; cells inside the outer but outside the inner have depth 1; cells inside the inner frame have depth 2. Frame outlines themselves are color 1 (initially). All other cells are 0. Rule (PAINT EACH CELL'S DEPTH+1 ACCORDING TO FRAME NESTING): keep color-1 frame cells AS 1. For EACH 0-cell, COMPUTE its DEPTH = number of color-1 rectangular frames that strictly contain it. PAINT the cell with COLOR (depth + 1) using a fixed depth→color mapping per demos (e.g., depth 0 → color 1, depth 1 → color 2, depth 2 → color 3, etc.). Net: the nested rectangle structure becomes a layered cake of concentric colored bands inside the original color-1 frames.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
