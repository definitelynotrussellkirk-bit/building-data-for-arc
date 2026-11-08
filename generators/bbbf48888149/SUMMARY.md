# bbbf48888149

0-bg grid (h~8-11, w~9-12) with exactly 3 ISOLATED 4-conn BLOBS in distinct colors with strictly distinct sizes (drawn from {2..6}). Blobs are non-touching. Rule: identify all 4-conn non-bg objects, pick the one with the SMALLEST cell count (unique by construction), crop to its bounding box, and UPSCALE by factor 2 (each cell becomes a 2×2 block of the same color). Output dimensions = (2 * bbox_h) × (2 * bbox_w).

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
