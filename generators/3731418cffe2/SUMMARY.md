# 3731418cffe2

0-bg grid (h~9-11, w~10-12) with: (a) an INDEX MARKER k at (0, 0) drawn as a single non-bg cell in some color (k ∈ 1..N where N = number of blobs); (b) N=3-4 disjoint CONNECTED BLOBS at random interior positions, each in a distinct non-{0, k} color and each with a distinct size from a small size-pool. Blobs are 4-adjacency-isolated. Rule: (1) CLEAR the index marker at (0, 0). (2) SORT the remaining blobs lexicographically by (size ASC, color ASC, top-row r1 ASC, left-col c1 ASC). (3) SELECT the k-th blob (1-indexed) under that ordering. (4) CROP the original grid to that blob's axis-aligned BBOX and output the cropped subgrid. Net: tiny output that's a bounding-box extract of one rank-selected blob.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
