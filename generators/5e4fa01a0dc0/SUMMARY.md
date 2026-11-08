# 5e4fa01a0dc0

0-bg grid with a few color-5 wall structures (lines, crosses, L-shapes, blocks) acting as BFS obstacles. Three markers 2, 3, 4 placed in open cells such that 4-connected BFS paths 2→3 and 3→4 are obstructed by at least one wall — forcing detours. Rule: BFS shortest path from 2 to 3 (4-connected, avoiding 5-walls). BFS shortest path from 3 to 4. Paint the union of all cells lying on any shortest path of both legs to color 8 (only cells that were 0; walls + markers preserved).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
