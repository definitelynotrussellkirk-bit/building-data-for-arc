# 026edc506fe6

0-bg grid (h~6-10, w~10-14) with: (a) a 4-conn SHAPE of color 1 (blue), 2-5 cells; (b) exactly ONE color-2 (red) single-cell MARKER 'a'; (c) exactly ONE color-3 (green) single-cell MARKER 'b'. The translated shape stays in-bounds and doesn't overlap existing non-bg cells. Rule: compute delta = (b_row - a_row, b_col - a_col). For every color-1 cell (r, c), paint output[r+dr][c+dc] = 4 (yellow). Original color-1 cells, the red marker, and the green marker stay in place. Net: a color-4 copy of the blue shape appears translated by the red→green vector.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
