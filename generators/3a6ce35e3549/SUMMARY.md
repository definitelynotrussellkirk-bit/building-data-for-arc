# 3a6ce35e3549

0-bg grid (h, w ~10-16) with: (a) FOUR DOTS at the corners of an axis-aligned rect (rh × rw, rh, rw ~5-8) in a MINORITY color; (b) a BLOB of 5+ cells strictly INSIDE the rect in a MAJORITY color. Two distinct non-bg colors total. Rule: identify the 4 corner-dot cells (minority color = dot color). Find the rectangle they define. Crop the rect's INTERIOR (strictly inside the 4 corner positions). Recolor the blob from majority (big) color to MINORITY (dot) color. Output: the cropped interior with the recolored blob.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
