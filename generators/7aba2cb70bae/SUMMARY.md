# 7aba2cb70bae

0-bg grid with N (3-5) separated color-7 components, each occupying a small connected region. Each component's bounding box touches some number of grid borders (top, bottom, left, right) — 0, 1, 2, 3, or 4. Rule: for each color-7 component, count its border-touch number K. If K == 1, recolor that component's cells to color 8. Otherwise (K in {0, 2, 3, 4}), keep the component as color 7. Output is the input with exactly-1-border components recolored 8; all other cells unchanged.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
