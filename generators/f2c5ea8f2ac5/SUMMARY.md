# f2c5ea8f2ac5

0-bg grid (h~7-10, w~8-11) with 2 NON-ZERO BLOBS in 2 distinct colors from {1..9}, located in the INTERIOR — at LEAST 1 all-zero row above and below the content, and at LEAST 1 all-zero col left and right of the content. Blobs are 2-4 cells each, placed at non-touching interior positions. Rule (CROP TO THE BBOX OF ALL NON-ZERO CELLS): COMPUTE min_r = minimum row of any non-zero cell, max_r = maximum row, min_c = minimum col, max_c = maximum col. OUTPUT is the SUBGRID from (min_r, min_c) to (max_r, max_c) INCLUSIVE — i.e., the rectangle tightly wrapping all non-zero content (cell colors preserved). Output dimensions = (max_r - min_r + 1) × (max_c - min_c + 1). Net: input is trimmed to its active bbox, dropping zero-padding.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
