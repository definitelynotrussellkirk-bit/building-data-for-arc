# 453ac12fbe96

0-bg grid (h~6-8, w~14-16) with EXACTLY 3 distinct-colour shapes at horizontal slots (1,1),(1,6),(1,11), each a VARIED connected polyomino (3-4 cells, bbox <=3 wide, always containing its (0,0) corner so the normalized sets share >=1 cell). Rule: normalize each shape's cells to (0,0); over the union bbox, colour each cell by overlap count: 2 shapes share -> 2, 3 shapes share -> 8, else 0. Varied shapes -> varied overlap-count map.

Kind: `per_puzzle`. Imported version: `3.1.1`.
Approval is derived by the catalog from current code and retained evidence.
