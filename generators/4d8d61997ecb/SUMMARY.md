# 4d8d61997ecb

0-bg grid (size varies). Cell (0,0) holds a ROTATION CODE in {1,2,3,4}. One TEMPLATE object (a random connected polyomino, 3-8 cells, the largest non-{0,9,code} object) sits in the grid, plus 2-4 color-9 MARKER cells positioned with room for the rotated stamp. Rule: rotate the template by the code (1=id, 2=cw, 3=180, else=ccw) and stamp it (top-left anchored) at every color-9 marker on a blank output. Output = the rotated template repeated at the marker positions.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
