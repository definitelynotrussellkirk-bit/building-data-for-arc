# 287285d0145f

0-bg grid (h~6-10, w~6-10) with: (a) SCATTERED RED (COLOR 2) CELLS — 2-6 cells placed on a small set of DISTINCT ROWS (1-4 rows total): each red cell at a random column on one of the selected red_rows; (b) SCATTERED GREEN (COLOR 3) CELLS — 2-6 cells placed on a small set of DISTINCT COLS (1-4 cols total): each green cell at a random row on one of the selected green_cols. Red and green cells don't share positions. Rule (INTERSECTION OF RED ROWS WITH GREEN COLS, PAINTED WITH COLOR 8): compute rs = SET OF DISTINCT ROW INDICES of all RED CELLS in the input. compute cs = SET OF DISTINCT COLUMN INDICES of all GREEN CELLS. PRODUCE a fresh same-size grid of 0s; for EVERY (r, c) WHERE r ∈ rs AND c ∈ cs: PAINT output[r][c] = COLOR 8 (cyan). Net: red markers broadcast horizontally, green markers broadcast vertically; their grid intersection becomes a cyan dot pattern on a blank canvas.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
