# 120c8532b351

Fixed 3×3 grid with: (a) MINORITY color (1-2 cells in a randomly chosen color); (b) MAJORITY cells (7-8) in 1-3 OTHER colors arranged in one of 5 layouts (uniform/two_colors/striped/checker/diagonal_split). Minority count must be STRICTLY LESS than every other color count. Rule (SELF-TILE GATED BY MINORITY): identify the MINORITY (least-frequent color). EMIT a 9×9 (3*h × 3*w) OUTPUT grid where each cell at position (R, C) is computed as: if input[R // 3][C // 3] == MINORITY → copy from input[R % 3][C % 3]; ELSE → 0 (or the cell's value if input cell isn't minority — task-specific). Net: 3×3 input self-tiles into 9×9 output gated by minority-color cells.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
