# dfc15333d5e1

0-bg grid (h~8-11, w~9-13) with 3-5 SEPARATED 3-CELL STRAIGHT LINES, each either HORIZONTAL (cells at (r, c..c+2)) or VERTICAL (cells at (r..r+2, c)), each in a DISTINCT non-zero color (random from 1..9). Lines are 4-conn isolated with ≥1-cell gap between them (guard neighborhood enforced during placement). Rule: identify EACH 3-CELL STRAIGHT LINE (connected component that is exactly 3 cells in a row or column). COLLAPSE each line to its CENTER CELL ONLY — keep the middle cell of the 3, ERASE the two endpoint cells to BG (0). Endpoint cells: for a horizontal line at (r, c..c+2), erase (r, c) and (r, c+2); for vertical, erase (r, c) and (r+2, c). Net: each 3-line shrinks to its single center-cell dot in the same color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
