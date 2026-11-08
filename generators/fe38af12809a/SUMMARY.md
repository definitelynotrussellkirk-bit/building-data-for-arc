# fe38af12809a

0-bg grid with: (a) one CODE cell in row 0 with value 1 or 3 (the Manhattan radius k); (b) one RED (color-2) SEED cell anywhere below row 0 — the radius-k Manhattan diamond around it may run off the grid edges (a clipped/partial ring); (c) scattered decoration cells in colors {1,3,4..9} (never 2, never in row 0, never exactly on the ring). Rule: find the first 1/2/3 cell in row 0 → k. Find the first color-2 seed. For each cell, if its value is 0 OR 2 AND its Manhattan distance from the seed equals k, set it to 8. Other cells preserved.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
