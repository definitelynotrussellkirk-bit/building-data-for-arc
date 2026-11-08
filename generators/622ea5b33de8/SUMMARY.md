# 622ea5b33de8

0-bg grid (h~9-14, w~12-18) containing 3-5 small CONNECTED COMPONENTS, each in a DISTINCT non-zero color. Each component is 1-3 cells from a small shape bank (singletons, dominos, corners). Components are 4-conn isolated. SOME pairs are placed CLOSE (1-cell apart, so their 1-cell DILATED HALOES OVERLAP); others are FAR apart (no halo overlap). Rule: SORT the N components in TOP-LEFT scan order. Build an N×N ADJACENCY MATRIX: diagonal[i][i] = component i's COLOR; off-diagonal[i][j] = 8 if i and j's 1-cell DILATED HALOES OVERLAP (1-cell apart or closer), else 0. Net: input is scattered colored components; output is a small N×N matrix encoding pairwise dilation-adjacency.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
