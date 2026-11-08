# b15542192542

0-bg grid (h~8-11, w~9-12) with 2-3 BLOBS in distinct non-bg colors. Each blob is a connected polyomino of 3-5 cells with a NON-TRIVIAL bbox (min bbox dimensions 2×2, so corners are not collinear). Blobs are 4-conn isolated. Rule: for each blob, compute its axis-aligned BOUNDING BOX (rmin, cmin, rmax, cmax). REPLACE the entire blob with EXACTLY 4 CELLS at its bbox CORNERS — (rmin, cmin), (rmin, cmax), (rmax, cmin), (rmax, cmax) — painted in the blob's original color. ERASE all other cells of the blob to 0. Net: each blob becomes 4 corner dots marking the bbox extremes; the blob's interior + edges vanish.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
