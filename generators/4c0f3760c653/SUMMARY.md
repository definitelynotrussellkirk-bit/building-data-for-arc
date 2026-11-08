# 4c0f3760c653

0-bg grid (h~7-10, w~9-12) with 3 BLOBS of varied aspect ratios placed at scattered positions in distinct non-zero colors from a 3-color palette: (a) a 2×2 SQUARE-bbox blob (h == w); (b) a VERTICAL 1×3 line (h ≠ w); (c) a HORIZONTAL 1×3 line (h ≠ w). Blobs are 4-conn isolated with 1-cell padding. Rule: for EACH CONNECTED BLOB, compute its bbox (rmax-rmin+1, cmax-cmin+1). KEEP only blobs with SQUARE BBOX (h == w). CLEAR (set to 0) all non-square blobs. Net: square-bbox blobs survive at their original color; non-square blobs are erased.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
