# 0c4e95ad76e7

0-bg grid (h, w ~9-14) with 2..4 SOLID FILLED OBJECTS in distinct non-bg colors, at RANDOM non-overlapping positions and VARIED sizes. Most are filled rectangles (≥3×3 so they have interior cells); some are fat irregular blobs (L / plus / random fill) that still enclose interior. Objects are isolated by ≥1 bg cell. Rule: for each object, compute its BOUNDARY cells (a cell with ≥1 4-neighbor outside the object), paint them on a fresh same-size grid in the object's color, interior → 0. Net: each solid object becomes its outline. Object count, sizes, shapes and positions all vary.

Kind: `per_puzzle`. Imported version: `3.0.2`.
Approval is derived by the catalog from current code and retained evidence.
