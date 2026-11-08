# ee850e92b585

0-bg grid (h~8-11, w~9-12) with 3 BLOBS of STRICTLY DISTINCT SIZES drawn from {2, 3, 4, 5, 6} via blob-walk, each in a DISTINCT non-rank color from {4, 5, 7, 9} (rank colors are {1, 2, 3} so input colors don't overlap output ranks). Blobs placed at non-overlapping positions. Rule (RANK BLOBS BY AREA ASCENDING, RECOLOR BY RANK 1, 2, 3): identify all BLOBS. SORT by SIZE ASCENDING (smallest first). RECOLOR the i-th smallest blob to COLOR i+1 (i.e., smallest → 1, next → 2, largest → 3). Net: blobs ranked small→large, recolored 1→2→3.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
