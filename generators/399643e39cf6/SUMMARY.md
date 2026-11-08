# 399643e39cf6

0-bg grid (h ∈ 8-10, w ∈ 9-11) with: (a) TWO COLOR-9 MARKERS at FIXED positions — g[0][1] and g[5][4] (define a translation delta = (5, 3)); (b) TWO BLOBS in DISTINCT colors at FIXED positions and shapes: SMALL BLOB (3-cell L-tromino) at (1, 1) painted COLOR 2 — cells (1,1), (1,2), (2,1); LARGE BLOB (3-cell L-tromino with different orientation) at (3, 3) painted COLOR 7 — cells (3,3), (4,3), (4,4). Rule (READ THE TWO 9-MARKERS' POSITIONS → COMPUTE DELTA VECTOR = SECOND_MARKER - FIRST_MARKER; FIND THE SMALLEST NON-9 BLOB (BY CELL COUNT, TIE-BREAK BY POSITION); REMOVE BOTH 9-MARKERS; COPY THE SMALLEST BLOB BY THE DELTA — STAMP IT AT POSITION + DELTA IN ITS ORIGINAL COLOR; THE ORIGINAL BLOB AND OTHER BLOBS STAY): LOCATE the 9-markers; COMPUTE v. FIND the smallest non-9 blob. REMOVE markers. PAINT the smallest blob's cells at (r + v.r, c + v.c). Net: smallest blob duplicated by vector; markers vanish.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
