# 671181efb2a3

0-bg grid (h~7-10, w~8-12) with a MIX of (a) 2-3 same-color CLUSTERS (each = a 2-cell ORTHOGONAL pair: two cells of the same color placed horizontally or vertically adjacent); (b) 2-4 isolated SINGLETON noise cells in various colors, placed with no same-color orthogonal neighbor. Cluster cells and singletons are spaced so they don't touch each other. Rule: for every non-bg cell, check if it has at least one ORTHOGONAL neighbor of the SAME COLOR. If yes (cluster member), PRESERVE. If no (singleton), ERASE (set to 0). Net: same-color orthogonal pairs survive; all isolated color noise is wiped.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
