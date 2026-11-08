# f46ea0247e29

0-bg grid (h~10-16, w~12-20) with 2-4 NON-BG OBJECTS at non-touching positions, each in a DISTINCT color from draw_distinct_colors. Each object has min_object_w ≥ 3 (rectangles, L/T/U shapes, tall_rect, or wide_rect). Objects placed with margin ≥1. Rule (ERASE TWO LEFTMOST COLUMNS OF EACH OBJECT): for EACH non-bg CONNECTED COMPONENT, COMPUTE its BBOX. For columns c = bbox_c1 and c = bbox_c1+1 (the two LEFTMOST columns of the bbox), CLEAR every cell of the object in those columns to BG (0). The remaining object cells (cols c1+2..c2) stay. Net: each object loses its 2 leftmost bbox columns, trimmed from the left.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
