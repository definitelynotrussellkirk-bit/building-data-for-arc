# 8a35d7908b42

0-bg grid (h~8-11, w~9-12) with 2-4 CONNECTED BLOBS each a 3-5 cell 4-connected component grown via grow_blob, painted in a DISTINCT non-0 color drawn from {1..9}. Blobs are placed at non-touching positions (tracked in used set) AND have STRICTLY DISTINCT BBOX CENTERS (integer division: center = ((rmin+rmax)//2, (cmin+cmax)//2)). Blobs are size ≥ 3 so the reduction rule is non-identity. Rule (REPLACE EACH BLOB WITH A SINGLE CELL AT ITS BBOX CENTER): for EACH 4-CONNECTED non-bg BLOB of color C: COMPUTE its bbox (r1, c1, r2, c2). COMPUTE the BBOX CENTER cr = (r1+r2) // 2, cc = (c1+c2) // 2. CLEAR every cell of the blob to bg-0. PAINT the single cell (cr, cc) with COLOR C. Other blobs are reduced independently. Net: each multi-cell colored blob collapses into a single-cell marker at its bbox center, preserving color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
