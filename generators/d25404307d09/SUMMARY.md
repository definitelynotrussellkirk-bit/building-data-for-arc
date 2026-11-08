# d25404307d09

0-bg grid (h, w ~10-13) with 3 SEPARATED 4-cell objects in distinct colors at fixed origins (1, 1), (1, w-5), (h-5, 2). Each object is an L-tetromino-style shape (3-4 cells) with asymmetric bbox. Rule: for each 4-conn non-bg object: crop to its BBOX (bbox_h × bbox_w). Rotate the cropped subgrid 90° CLOCKWISE. Paste the rotated subgrid back at the SAME origin (top-left of original bbox) — note rotated bbox is bbox_w × bbox_h, may extend differently than original. Net: each object appears rotated 90° CW in place at its bbox top-left anchor.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
