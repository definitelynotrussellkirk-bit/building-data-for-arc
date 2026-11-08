# ea56ba328a3e

0-bg grid with several separated color-2 components. Each component may be SOLID (no enclosed 0-regions) or have N (≥1) INTERIOR HOLES (4-conn 0-regions fully enclosed by 2-cells, not touching the grid border through 0-bg). Rule: keep only color-2 cells; compute connected components; for each component count its topological holes h; recolor its cells in the output to: h=0 → 3, h=1 → 4, h=2 → 5, h=3 → 6, h≥4 → 9. Original 2-cells are dropped (the count-based color replaces them). Empty cells stay 0.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
