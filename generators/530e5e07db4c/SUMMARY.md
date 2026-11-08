# 530e5e07db4c

0-bg grid (h~6-8, w~9-11) with: (a) one RED(2) SEED; (b) one BLUE(3) SEED; (c) a connected PATH of GRAY(5) cells linking them (4-connected through cells with value ∈ {2, 3, 5}); (d) 1-2 ISOLATED GRAY(5) STUB cells elsewhere, not connected to the path. Path orientations vary (horizontal, vertical, L, diagonal-by-stair). Rule: BFS from the 2-seed through cells with value in {2, 3, 5} (4-connectivity). If the BFS reaches the 3-seed → for every 5-cell in the reachable component, recolor it to YELLOW(4). Else output unchanged. Isolated 5-stubs stay as 5 (not reachable, not recolored).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
