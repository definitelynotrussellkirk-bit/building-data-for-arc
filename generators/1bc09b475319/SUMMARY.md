# 1bc09b475319

0-bg grid (h~9-13, w~11-15) with 3-6 HORIZONTAL color-6 (magenta) BARS. Each bar: a contiguous run of color-6 cells in a single row, length 2-5. Bars live in distinct rows (no two bars share a row). Bars may abut a grid edge or have bg on both sides. Rule: for each cell (r, c), if v == 0 AND either (a) (r, c+1) and (r, c+2) are both 6 (left cap of a bar) OR (b) (r, c-1) and (r, c-2) are both 6 (right cap of a bar) → paint 8 (cyan). Otherwise keep the input value. Net effect: paint a cyan 'cap' at each open end of every bar; bars themselves stay 6.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
