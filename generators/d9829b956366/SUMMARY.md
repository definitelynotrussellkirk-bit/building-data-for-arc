# d9829b956366

0-bg grid (h~6-8, w~8-10) containing 2-4 CONNECTED MOTIFS of 2-4 cells each, all painted in COLOR 4 (yellow). Half of them (ceil(n/2)) TOUCH the GRID BORDER (any cell at row 0, row h-1, col 0, or col w-1); the other half are placed in the INTERIOR (no border contact). Motifs are non-touching (separated by ≥1 cell padding). Rule: for every CONNECTED COMPONENT, check if any of its cells touches the grid BORDER (row 0, row h-1, col 0, or col w-1). If YES, RECOLOR every cell of that component to COLOR 2 (red). If NO (entirely interior), leave the component as color 4 (yellow). Net: border-touching motifs become red; interior motifs stay yellow.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
