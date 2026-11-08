# 5e5205e54c96

Fixed 15×15 grid with: (a) ROW 0 holding a LEGEND of 2-3 DISTINCT non-{8} colors at cols 0..depth-1 (outer-to-inner order); (b) NESTED COLOR-8 (cyan) FRAMES at depth hardcoded boxes _BOXES = [(2, 2, 14, 14), (5, 5, 11, 11), (7, 7, 9, 9)]; frames drawn for depth=2-3 (outer + inner). Each frame is a hollow color-8 rectangle. Interior between frames is 0. Rule (NESTED-FRAME FILL BY LEGEND): for EACH frame in outer-to-inner order (matching the row-0 legend order), use the corresponding LEGEND COLOR to: (1) recolor the frame's color-8 cells to that legend color OR (2) fill the annular region inside that frame (between this frame and the next inner frame) with that color. The deepest legend color fills the innermost 0-region. Net: each nested ring fills with its depth-indexed legend color.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
