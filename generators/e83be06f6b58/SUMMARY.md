# e83be06f6b58

Color-7 (orange) BACKGROUND grid (row_count~4-7, w~8-12). Each row contains a visible RUN of 3-5 cells using two ALTERNATING non-7 colors {a, b} from a palette, where a < b. Rows alternate which color STARTS the run: even rows start with a (smaller); odd rows start with b (larger). Run start column and length vary per row. Rule: examine each row's visible run. If the run STARTS with the MAX of the two colors (the larger one), SHIFT the entire row's run ONE CELL RIGHT (i.e., the leftmost cell becomes 7-bg, the rightmost shifts into the cell right of the previous end). If it starts with the min color, leave the row unchanged. Net: max-starting rows slide right by 1; min-starting rows stay.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
