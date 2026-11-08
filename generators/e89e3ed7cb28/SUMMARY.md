# e89e3ed7cb28

0-bg grid (h~7-10, w~8-12) with 4-7 ACTIVE COLUMNS. Each active column contains 1-3 non-bg cells stacked vertically at random rows, in distinct non-bg colors per cell. Other columns are empty. Rule: for each column, find the BOTTOMMOST non-zero cell (the cell at the largest row index in that column). KEEP only that bottommost cell; erase all other non-zero cells in the same column to 0. Empty columns stay empty. Net: gravity-prune — each active column drops its upper cells and retains only the lowest one (the bottommost color survives, others vanish).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
