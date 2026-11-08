# d06e81a85b9e

0-bg grid (h~7-9, w~9-11) with: 2-3 cells of color 2 (red), 2-3 cells of color 3 (green), and 1-3 scattered distractor cells (colors {1, 4, 5, 6, 7, 9}). All cells are placed at random distinct positions. Rule: produce a FRESH same-shape grid where each cell (r, c) is 8 (cyan) if: (a) input[r][c] == 0; (b) there exists a 2-cell at (r, c2) on the same row with all cells strictly between c and c2 in that row equal to 0 (horizontal LoS to a red); (c) there exists a 3-cell at (r2, c) on the same column with all cells strictly between r and r2 equal to 0 (vertical LoS to a green). Else cell is 0. The 2/3/distractors do NOT appear in the output.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
