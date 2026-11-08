# 8bbb30a8fc2f

0-bg grid (h, w~8-14) with 3-5 BLOBS each of a DISTINCT SIZE (sampled from ascending/wide-spread/tight-spread distributions over sizes ~1-9) in DISTINCT COLORS from {1, 3, 4, 5, 6, 7, 8, 9} (NOT color 2, since 2 is the rule's output). Blobs are non-touching (4-conn separation). The SMALLEST BLOB has a STRICTLY UNIQUE size (no tie at minimum). Rule (FIND SMALLEST OBJECT BY SIZE, RECOLOR TO 2): find every 4-CONNECTED NON-0 COMPONENT. COMPUTE the CELL COUNT of each. IDENTIFY the COMPONENT with MINIMUM size. RECOLOR ALL its cells to COLOR 2 (red). Other components stay unchanged. Net: the smallest blob turns red; all others keep their colors.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
