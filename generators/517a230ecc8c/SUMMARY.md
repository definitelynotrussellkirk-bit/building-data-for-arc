# 517a230ecc8c

0-bg grid (h~8-13, w~10-15) with 2-3 BLOBS of 2-4 cells each (4-connected, grown via grow_blob), each in a DISTINCT non-0 color drawn from {1..9}. Blobs are placed STRICTLY IN THE INTERIOR (excluding the outer border row/column — added to `used` set before growing) so their 1-step halos won't extend off-grid. Blobs are spaced apart by ≥2 cells (via 2-cell dilation check) so their halos do NOT touch each other or overlap. Rule (EXPAND EACH BLOB BY ONE CELL IN 4 CARDINALS — PAINT EACH HALO CELL ITS BLOB'S COLOR): for EACH bg-0 cell in the input: INSPECT its 4 ORTHOGONAL NEIGHBORS. IF all neighbors are 0 → leave the cell as bg-0; IF all NON-0 neighbors share the same color C and at least one neighbor is non-0 → PAINT this cell with C (the halo color). IF neighbors have multiple distinct non-0 colors → the rule is undefined (but the input is constructed so this never happens). The original blob cells stay their colors. Net: each blob is dilated by 1 cell in the 4 cardinal directions, growing a single-cell halo around it.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
