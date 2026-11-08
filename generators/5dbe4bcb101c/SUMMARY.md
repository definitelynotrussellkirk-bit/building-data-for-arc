# 5dbe4bcb101c

0-bg grid (h~7-12, w~10-15) with: (a) ONE COLOR MARKER CELL in row 0 at random col mc — color drawn from 2..9 (the 'marker color'); (b) 1-2 MARKER-COLOR BLOBS of size 2-5 placed at row r ≥ 2 (avoiding marker row); (c) 1-3 DISTRACTOR BLOBS in different colors at rows ≥ 2; (d) optionally 1-3 MARKER-COLOR SINGLETONS scattered (rule ignores these). Rule (MARKER-COLOR TOPMOST CROP): READ row 0 to find the MARKER COLOR (first non-zero cell's value). Among ALL CONNECTED COMPONENTS in the body (rows ≥ 1) with COLOR == MARKER AND SIZE > 1, pick the TOPMOST one (min r1, then min c1 as tiebreaker). EMIT the BBOX CROP of that component as the output (a small subgrid with the blob in place, bbox padded with 0 if applicable). Singletons ignored. Net: row-0 marker color picks the topmost matching blob; output is its bbox crop.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
