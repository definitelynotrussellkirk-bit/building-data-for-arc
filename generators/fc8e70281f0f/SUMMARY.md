# fc8e70281f0f

0-bg grid: row 0 holds K color-1 cells (K = the target articulation count). Below row 0 are one or more CHAINS of touching cells in distinct colors — a chain of m cells is a path of m objects with m-2 ARTICULATION objects (cut vertices of the object-adjacency graph). Exactly one chain has m-2 == K. Rule: count the row-0 ones (K); group body objects into clusters by adjacency; find the cluster whose articulation count equals K; OUTPUT its union (bbox crop) recolored to 8.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
