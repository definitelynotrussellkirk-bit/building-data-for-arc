# 1563be9f6591

Multicolor grid (h, w~5-10) with PALETTE OF 3-6 DISTINCT COLORS (EXCLUDING 7) where: (a) TOP-1 color has ~30-45% of cells; (b) TOP-2 color has ~20-30% of cells; STRICTLY top1_count > top2_count > each minor count (gap ≥1); (c) remaining MINOR colors fill the rest in a layout (uniform/ascending/single/long-tail) and arrangement (random/stripes/block/checker/gradient). Color 7 NEVER appears in input. Rule (KEEP TOP-2 MOST FREQUENT, RECOLOR REST TO 7): compute COLOR-COUNTS over the grid. Identify the TOP-2 most frequent colors. For EACH cell: if its color is in TOP-2, KEEP. Else, RECOLOR to 7. Net: rare minority colors all become 7; dominant duo survives.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
