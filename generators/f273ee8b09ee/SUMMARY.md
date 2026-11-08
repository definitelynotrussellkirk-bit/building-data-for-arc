# f273ee8b09ee

0-bg grid (h×w, ~8-14 by ~11-16) with 3 connected BLOBS normally and 3-4 at hard difficulty, in distinct non-zero colors, varied shapes (2-4 cells each). Blobs 8-conn isolated. Rule: detect all components. Sort by bbox top-left (row asc, then col asc). For each blob, crop to its bbox. Horizontally concatenate the crops (left-to-right in sort order) with 1-col gaps. Output height = max(crop heights); width = sum(crop widths) + (n-1) gaps. Each blob's color preserved in its slot.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
