# 1e41c90ec2dc

0-bg grid (h, w~8-12) with 2-4 NON-TOUCHING BBOX-ISOLATED BLOBS, each grown to size 3-6 cells, in DISTINCT colors shuffled from {1..9}. Blobs are placed so their BBOXES DON'T OVERLAP (strict bbox isolation, not just 4-non-touching) and ≥1 blob is NOT 180°-symmetric so the rule produces visible change. Rule (UNION EACH BLOB WITH ITS 180° ROTATION WITHIN BBOX): For EACH BLOB: COMPUTE its BBOX (r1, c1, r2, c2). For EACH cell at (r, c) of the blob, PAINT the 180°-ROTATED position (r1+r2-r, c1+c2-c) in the SAME color. Original cells stay (so the result is the UNION of the blob and its 180° rotation within bbox). Net: each blob becomes its own 2-fold rotationally symmetric version inside its bbox.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
