# 102e79f0ca6d

0-bg grid (h ∈ 9-12, w ∈ 10-13) with: (a) TWO EDGE-TOUCHING COMPONENTS of DIFFERENT COLORS at a random interior position, configured per contact_orientation ∈ {horizontal, vertical}: HORIZONTAL: a COLOR-2 (red) vertical 3-cell strip and an ADJACENT COLOR-3 (green) horizontal 2-cell extension touching the middle right of the red strip; VERTICAL: a COLOR-2 horizontal 3-cell strip and a COLOR-3 vertical 2-cell extension touching the middle bottom; (b) ONE ISOLATED COLOR-6 MAGENTA COMPONENT at (h-2, w-3..w-2) — a 2-cell distractor that does NOT touch the other two. Rule (KEEP ONLY NON-BG CELLS THAT EDGE-TOUCH A DIFFERENT-COLORED COMPONENT, RECOLOR THEM TO COLOR 8; OTHERS BECOME 0): For EACH non-bg cell (r, c) with color k: CHECK its 4-neighbors. IF ANY neighbor has a non-bg color != k: PAINT g[r][c] = COLOR 8 (cyan). ELSE: PAINT 0. Isolated components (no different-colored neighbor) are erased entirely. Net: only the inter-color contact boundary survives, painted in cyan.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
