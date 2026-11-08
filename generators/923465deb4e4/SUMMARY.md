# 923465deb4e4

0-bg grid (h~8-11, w~9-12) with: (a) cell (0,0) = KEY (some non-bg color); (b) one 3-5 cell BLOB of the KEY color placed elsewhere on the grid (away from (0,0)); (c) 1-2 DISTRACTOR blobs in different colors. Rule: read key = grid[0][0]. Clear (0,0) to 0 (temp). Find all cells in temp matching the key color. If none → output [[0]]. Else: compute bbox of those key-color cells. Output: temp cropped to that bbox (small grid containing the key blob plus any distractor cells that happen to lie inside the same bbox).

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
