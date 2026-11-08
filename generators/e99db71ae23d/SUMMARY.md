# e99db71ae23d — Diagonal L-Tromino Projections

Each lawful input has a color-7 background and separated three-cell L-trominoes in gray (`5`) and red (`2`). The missing corner of each 2×2 bounding box defines an opening. Gray objects project a yellow (`4`) copy one diagonal cell toward the opening; red objects project a green (`3`) copy one diagonal cell away. Off-grid projected cells are clipped, and green overwrites yellow where cross-color projections collide.

Kind: `per_puzzle`. Selected version: `3.2.0`. Canonical `RULE_HASH`: `32f38f665cc3`.

The default four-pair lesson is intentionally ordered:

1. randomized all-orientation demonstration (`general_orientation_8`),
2. randomized clipping-plus-collision demonstration (`general_edge_overlap_6`),
3. randomized collision-priority demonstration (`general_overlap_8`),
4. a difficulty-weighted varied query.

The hard query sampler retains exact canonical support through `public_dense_16` without replaying a fixed canonical grid as a demonstration. Executable competitors cover swapped directions, both colors moving toward, both moving away, and yellow-winning collisions. Clipping and full orientation support are declared as branch-coverage witnesses rather than mislabeled rival refutations.

Final generator SHA-256: `c811b7c51c933fbdd410606ad97d98fec6d2f85046c88ecca6b5b4b8e04a01dd`.
