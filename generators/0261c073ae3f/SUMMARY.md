# 0261c073ae3f

Grid split by a single full color-5 column into 2 panels. Each panel holds a non-zero compact object pattern in some non-bg, non-5 color. Rule: extract left panel and right panel (as subgrids). Normalize each: crop to bbox of non-zero cells, then convert to binary mask. Take XOR of the two binary masks (aligned at (0,0), padded by 0 where dims differ). Output is the bbox-sized XOR with 7 wherever the masks differ, 0 wherever they match.

Kind: `per_puzzle`. Imported version: `1.3.2`.
Approval is derived by the catalog from current code and retained evidence.
