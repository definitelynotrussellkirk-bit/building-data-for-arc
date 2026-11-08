# ddeaf19c698d

0-bg grid (h~6-9, w~7-11) with 3-5 SINGLETON SEEDS at random positions, each in a DISTINCT non-zero color (drawn via distinct_colors). Seeds are placed with a 3-cell HORIZONTAL BRUSH neighborhood guard ((r, c-1..c+1)) so brushes don't overlap. Rule (HORIZONTAL BRUSH EXPANSION): for EACH SINGLETON SEED at (r, c) with color C, PAINT a HORIZONTAL 3-CELL BRUSH at row r, cols c-1, c, c+1 — i.e., paint (r, c-1), (r, c), (r, c+1) with color C. CLIP at grid edges (cells outside 0..w-1 are dropped). Net: each singleton dot expands into a 1×3 horizontal stripe in its color.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
