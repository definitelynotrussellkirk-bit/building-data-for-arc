# cdaa7a006471

0-bg grid (h ∈ 9-11, w ∈ 11-13) with: N ∈ 3-4 DISTINCT-COLOR BLOBS, each a 3-5 cell irregular blob built via grow_blob random walk, painted in DISTINCT colors drawn from {5,6,7,8,9}, placed at non-overlapping positions where each blob has a STRICTLY NEAREST border (no tie among top, bottom, left, right) — _nearest_unique check enforces this. Rule (FOR EACH BLOB, COMPUTE THE DISTANCE FROM ITS BBOX TO EACH OF THE 4 GRID BORDERS (TOP, BOTTOM, LEFT, RIGHT); RECOLOR THE BLOB BY THE NEAREST BORDER: TOP→COLOR 1, BOTTOM→COLOR 2, LEFT→COLOR 3, RIGHT→COLOR 4; TIES KEEP ORIGINAL COLOR): For EACH blob with bbox (r1, c1, r2, c2): COMPUTE distances (r1, h-1-r2, c1, w-1-c2). FIND the UNIQUE minimum (top=0, bottom=1, left=2, right=3). RECOLOR every cell of the blob by that border index (0→1, 1→2, 2→3, 3→4). On tie: keep original color. Net: blobs recolored by which grid border is closest.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
