# 5998c17d89a0

0-bg grid with: (a) ONE KEY cell at (0,0) in color {1, 2, 3, 4+} specifying the boolean op (1=union, 2=intersection, 3=xor, else=a-minus-b); (b) EXACTLY 2 connected components A and B in the rest of the grid, in distinct non-{0, key} colors. A is placed leftmost (smaller leftmost col); B is rightmost. Both have the same bbox dimensions (so the boolean op is well-defined). Rule: apply the boolean op (key-determined) on the binary masks of A and B. Output is the resulting shape painted in color 8 (cropped to its bbox).

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
