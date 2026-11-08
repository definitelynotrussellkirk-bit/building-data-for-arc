# 9df67b512dad

Split the grid into nine zones: four singleton corners, four border strips with the corners removed, and the interior rectangle. Scan each zone in row-major order. Output a 3x3 grid containing the LAST NON-ZERO value seen in each zone, or 0 for an empty zone. Generated lessons use rotating empty-zone masks and multicolor scan conflicts so first-hit and occupancy-only shortcuts are refuted.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
