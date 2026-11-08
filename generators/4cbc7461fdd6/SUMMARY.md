# 4cbc7461fdd6

0-bg grid (h, w~6-14) with SPARSE GRAY(5) CELLS placed in a mix of two types: (a) 1-5 LR-SYMMETRIC PAIRS — each pair consists of cells at (r, c) and (r, w-1-c) (both painted 5, c ≠ w-1-c so they're distinct positions); (b) 1-5 ASYMMETRIC SOLO GRAYS — single cells at (r, c) with no partner at (r, w-1-c). Pair layout (random/cluster/row/column/diagonal) and solo layout vary independently. Rule (RECOLOR LR-SYMMETRIC GRAY PAIRS TO BLUE, LEAVE ASYMMETRIC GRAYS AS GRAY): For EACH GRAY (5) CELL at (r, c): check if the LR-MIRROR cell at (r, w-1-c) is ALSO 5. If YES (the cell has a partner): RECOLOR (r, c) from 5 to 1 (blue). Else (no partner — asymmetric solo gray), KEEP at 5. Other cells unchanged. Net: paired grays transform to blue; solo grays survive.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
