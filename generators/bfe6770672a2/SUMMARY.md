# bfe6770672a2

Grid laid out as a 4×4 MACRO-GRID of cell_size × cell_size (cell_size ∈ {1, 2}) macro-cells, separated by SEPARATOR rows/cols painted color `sep` (drawn from non-bg). Each macro-cell is one of: TARGET color, SUPPORT color, or empty. The input is configured so one TARGET macro-cell at (1, 1) has a distinctive SUPPORT neighborhood (its 4 cardinal macro-cells colored support); other TARGET macro-cells appear elsewhere without support. Rule: detect the target-color macro-cell with the strongest support neighborhood. Propagate that pattern (paint matching support neighbors) to every other target macro-cell.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
