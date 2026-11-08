# feeea4ae7af8

0-bg grid (size varies). Cell (0, 0) holds a COMMAND in {1, 2, 3, 4}. Rest of grid has 2-4 4-connected random polyomino objects in distinct colors, with PAIRWISE-DISTINCT size, bbox-width, and bbox-height (so every command is unambiguous). Rule: clear (0, 0) to 0. Compute objects of the cleared grid. Pick one object per command — 1: smallest size, 2: largest size, 3: widest bbox, 4: tallest bbox; tiebreakers go to top-most then left-most then smallest color. Output = bbox crop of the chosen object (paint its cells in its color over an empty grid sized to the bbox).

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
