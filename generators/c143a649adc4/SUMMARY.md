# c143a649adc4

0-bg grid (h~9-11, w~12-14) with 3-4 ISOLATED 4-CONN COMPONENTS, each a 2-or 3-cell shape (L-tromino/I-domino/square-corner) in a DISTINCT color from {1..9}. Components placed at scattered positions with varying Manhattan-2 neighborhood degrees (some isolated, some touching others). Rule (RECOLOR EACH COMPONENT BY ITS MANHATTAN-2 TOUCH DEGREE): For EACH COMPONENT: COUNT the number of OTHER COMPONENTS within MANHATTAN-2 distance (any pair of cells in different components with Chebyshev ≤ 2 or Manhattan ≤ 2). MAP DEGREE → COLOR: 0→2, 1→3, 2→4, 3→5, 4→6, ≥5→7. RECOLOR all component cells to the mapped color. Net: each shape repaints by how many neighbors it has within Manhattan-2.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
