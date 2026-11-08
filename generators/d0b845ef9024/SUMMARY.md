# d0b845ef9024

0-bg grid (h ~ 11-19, w ~ 10-22) with FG CELLS in one color drawn from {1..9}: (a) several CONNECTED CLUSTERS of varying shape (rect / L_shape / blob / cross / line_h / line_v) and size (small / medium / large / mixed) — each cluster's cells are 8-connected with at least one same-color neighbor; (b) many ISOLATED SINGLETON CELLS placed via one of 5 LAYOUTS (random / corners / row / column / scattered) at positions where their 8-neighborhood is clear of any other fg cells (so they're truly isolated). All fg cells share the same color. Rule (ERASE ISOLATED SAME-COLOR PIXELS — KEEP ONLY CELLS WITH AN 8-CONNECTED SAME-COLOR NEIGHBOR): for EACH fg CELL (r, c): CHECK its 8 SURROUNDING NEIGHBORS. IF at least ONE neighbor has the SAME COLOR: KEEP the cell. IF NO neighbor has the same color (isolated singleton): SET the cell to bg-0. Bg-0 cells stay 0. Net: connected clusters survive intact; isolated singletons are erased to bg-0.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
