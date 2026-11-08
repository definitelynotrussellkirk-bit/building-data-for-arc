# 2c4317f69f0a

0-bg grid (h~8-12, w~8-12) with EXACTLY 3 NON-TOUCHING COLOR-8 (cyan) BLOBS at scattered positions, with STRICTLY DISTINCT SIZES (3 unique values from 2..6, sorted ascending and placed via grow_blob). Blobs are 4-conn isolated. Rule (SIZE-RANK RECOLOR + ERASE OTHERS): identify the 3 COLOR-8 BLOBS. SORT them by SIZE ASCENDING. RECOLOR by rank: smallest → COLOR 2 (red), medium → COLOR 3 (green), largest → COLOR 4 (yellow). Other cells stay 0. Note: output starts from an empty grid (only the 3 recolored blobs remain in their positions). Net: 3 cyan blobs → ranked colors (2, 3, 4) by size; bg cells stay 0.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
