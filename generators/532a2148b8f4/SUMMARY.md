# 532a2148b8f4

0-bg grid (h~9-11, w~12-14) with 3-4 ISOLATED 4-conn COMPONENTS (1-3 cells each) in distinct non-bg colors, mixed near/far so some pairs share clear row/column line-of-sight while others do not. Rule: extract all 4-conn non-bg components, sort by top-left (r1, c1) ascending. For each pair, scan horizontally/vertically from every cell; if the first non-bg object seen after at least one 0-cell is the other component, they are adjacent. Output is an N×N matrix where N = number of components: diagonal[i][i] = 1 (blue); off-diagonal[i][j] = 8 (cyan) if line-of-sight holds, else 0. Net: a visibility matrix.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
